from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from loguru import logger

from fastmvc_dashboards._optional_import import optional_import

try:
    from configurations.workflows import WorkflowsConfiguration
except ImportError:
    WorkflowsConfiguration = None  # type: ignore[assignment, misc]

_temporal_mod, _temporal_client_cls = optional_import("temporalio.client", "Client")
_prefect_mod, _prefect_client_cls = optional_import("prefect", "Client")
_dagster_mod, _dagster_client_cls = optional_import("dagster_grpc", "DagsterGrpcClient")


class IWorkflowEngine(ABC):
    @abstractmethod
    async def start_order_workflow(self, order_id: str, tenant_id: str, payload: Dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_order_status(self, workflow_id: str) -> Dict[str, Any]:
        raise NotImplementedError


class TemporalWorkflowEngine(IWorkflowEngine):
    def __init__(self, address: str, namespace: str, task_queue: str) -> None:
        if _temporal_client_cls is None:
            raise RuntimeError("temporalio is not installed")
        self._address = address
        self._namespace = namespace
        self._task_queue = task_queue
        self._client: Any | None = None

    async def _ensure_client(self) -> Any:
        if self._client is None:
            self._client = await _temporal_client_cls.connect(
                self._address,
                namespace=self._namespace,
            )
        return self._client

    async def start_order_workflow(self, order_id: str, tenant_id: str, payload: Dict[str, Any]) -> str:
        client = await self._ensure_client()
        workflow_id = f"order-{tenant_id}-{order_id}"
        handle = await client.start_workflow(
            "OrderWorkflow",
            {"order_id": order_id, "tenant_id": tenant_id, "payload": payload},
            id=workflow_id,
            task_queue=self._task_queue,
        )
        return handle.id

    async def get_order_status(self, workflow_id: str) -> Dict[str, Any]:
        client = await self._ensure_client()
        try:
            handle = client.get_workflow_handle(workflow_id)
            info = await handle.describe()
            return {"workflowId": workflow_id, "status": str(getattr(info, "status", "unknown"))}
        except Exception as exc:
            logger.warning("Temporal get_order_status failed for %s: %s", workflow_id, exc)
            return {"workflowId": workflow_id, "status": "unknown", "error": str(exc)}


class PrefectWorkflowEngine(IWorkflowEngine):
    def __init__(self, api_url: Optional[str], default_deployment: Optional[str]) -> None:
        if _prefect_client_cls is None:
            raise RuntimeError("prefect is not installed")
        self._client = _prefect_client_cls(api=api_url) if api_url else _prefect_client_cls()
        self._deployment = default_deployment

    async def start_order_workflow(self, order_id: str, tenant_id: str, payload: Dict[str, Any]) -> str:
        if not self._deployment:
            raise RuntimeError("Prefect default deployment is not configured")
        flow_run = await self._client.create_flow_run_from_deployment(
            deployment_id=self._deployment,
            parameters={"order_id": order_id, "tenant_id": tenant_id, "payload": payload},
        )
        return str(flow_run.id)

    async def get_order_status(self, workflow_id: str) -> Dict[str, Any]:
        try:
            fr = await self._client.read_flow_run(workflow_id)
            return {"workflowId": workflow_id, "status": str(fr.state.type)}
        except Exception as exc:
            logger.warning("Prefect get_order_status failed for %s: %s", workflow_id, exc)
            return {"workflowId": workflow_id, "status": "unknown", "error": str(exc)}


class DagsterWorkflowEngine(IWorkflowEngine):
    def __init__(self, grpc_endpoint: str, job_name: str) -> None:
        if _dagster_client_cls is None:
            raise RuntimeError("dagster-grpc is not installed")
        self._client = _dagster_client_cls(grpc_endpoint)
        self._job_name = job_name

    async def start_order_workflow(self, order_id: str, tenant_id: str, payload: Dict[str, Any]) -> str:
        from asyncio import to_thread
        def _launch_sync() -> str:
            run = self._client.submit_job_execution(
                job_name=self._job_name,
                run_config={"ops": {"order_op": {"config": {"order_id": order_id, "tenant_id": tenant_id}}}},
                tags={"tenant_id": tenant_id},
            )
            return run.run_id
        return await to_thread(_launch_sync)

    async def get_order_status(self, workflow_id: str) -> Dict[str, Any]:
        from asyncio import to_thread
        def _status_sync() -> Dict[str, Any]:
            run = self._client.get_run(workflow_id)
            return {"workflowId": workflow_id, "status": run.status.value}
        try:
            return await to_thread(_status_sync)
        except Exception as exc:
            logger.warning("Dagster get_order_status failed for %s: %s", workflow_id, exc)
            return {"workflowId": workflow_id, "status": "unknown", "error": str(exc)}


def build_workflow_engine() -> Optional[IWorkflowEngine]:
    if WorkflowsConfiguration is None:
        logger.info("WorkflowsConfiguration not available (configurations.workflows).")
        return None
    cfg = WorkflowsConfiguration.instance().get_config()
    if not cfg.enabled:
        logger.info("Workflow engine is disabled in configuration.")
        return None

    if cfg.engine == "temporal":
        try:
            return TemporalWorkflowEngine(
                address=cfg.temporal_address,
                namespace=cfg.temporal_namespace,
                task_queue=cfg.temporal_task_queue,
            )
        except Exception as exc:
            logger.warning("Failed to initialize Temporal engine: %s", exc)

    if cfg.engine == "prefect":
        try:
            return PrefectWorkflowEngine(
                api_url=cfg.prefect_api_url,
                default_deployment=cfg.prefect_default_deployment,
            )
        except Exception as exc:
            logger.warning("Failed to initialize Prefect engine: %s", exc)

    if cfg.engine == "dagster":
        try:
            if not (cfg.dagster_grpc_endpoint and cfg.dagster_job_name):
                raise RuntimeError("Dagster endpoint and job name must be configured")
            return DagsterWorkflowEngine(
                grpc_endpoint=cfg.dagster_grpc_endpoint,
                job_name=cfg.dagster_job_name,
            )
        except Exception as exc:
            logger.warning("Failed to initialize Dagster engine: %s", exc)

    logger.info("No workflow engine could be initialized.")
    return None
