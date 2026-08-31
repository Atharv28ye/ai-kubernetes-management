from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger
import os
import sys


# Add backend directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


try:
    from services.investigation_service import InvestigationService
    from services.history_service import HistoryService

except ImportError as e:
    logger.error(
        f"Failed to import investigation services: {e}"
    )
    raise


router = APIRouter(
    prefix="/investigate",
    tags=["investigation"]
)


class InvestigationRequest(BaseModel):
    """Request model for Kubernetes investigation."""

    namespace: str = Field(
        default="all",
        description="Namespace to investigate"
    )

    collect_logs: bool = Field(
        default=True,
        description="Whether to collect logs from problematic pods"
    )

    max_log_lines: int = Field(
        default=100,
        description="Maximum number of log lines to collect per pod"
    )

    enable_ai: bool = Field(
        default=True,
        description="Whether to enable AI analysis"
    )

    cluster: Optional[str] = Field(
        default=None,
        description="Selected Kubernetes context/cluster"
    )


class TargetedInvestigationRequest(BaseModel):
    """Request model for targeted resource investigation."""

    resource_name: str = Field(
        ...,
        description="Name of the resource to investigate"
    )

    resource_type: str = Field(
        default="pod",
        description="Type of resource: pod, deployment, or service"
    )

    namespace: str = Field(
        default="default",
        description="Namespace of the resource"
    )

    enable_ai: bool = Field(
        default=True,
        description="Whether to enable AI analysis"
    )


# Initialize services
enable_ai_default = (
    os.getenv("ENABLE_AI", "true").lower() == "true"
)

investigation_service = InvestigationService(
    enable_ai=enable_ai_default
)

history_service = HistoryService()


@router.post("/")
async def investigate_cluster(
    request: InvestigationRequest
):
    """
    Run a full Kubernetes investigation across the cluster.
    """

    original_ai_setting = investigation_service.enable_ai

    try:
        logger.info(
            f"Received investigation request: "
            f"namespace={request.namespace}, "
            f"cluster={request.cluster}, "
            f"AI={request.enable_ai}"
        )

        # Temporarily override AI setting.
        investigation_service.enable_ai = request.enable_ai

        result = await investigation_service.investigate(
            namespace=request.namespace,
            collect_logs=request.collect_logs,
            max_log_lines=request.max_log_lines
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get(
                    "error",
                    "Investigation failed"
                )
            )

        # Determine cluster name.
        cluster_name = (
            request.cluster
            or os.getenv("CURRENT_CLUSTER")
            or "current-context"
        )

        # Save successful investigation to backend history.
        diagnosis = result.get("diagnosis")

        if diagnosis:
            try:
                history_service.save_investigation(
                    investigation_id=result.get(
                        "investigation_id",
                        "unknown"
                    ),
                    cluster=cluster_name,
                    namespace=request.namespace,
                    diagnosis=diagnosis,
                    status="completed"
                )

            except Exception as history_error:
                # History failure should NOT make the actual
                # Kubernetes investigation fail.
                logger.error(
                    f"Failed to save investigation history: "
                    f"{history_error}"
                )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error in investigation endpoint: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        # Always restore original AI setting.
        investigation_service.enable_ai = (
            original_ai_setting
        )


@router.get("/history")
async def get_investigation_history(
    limit: int = Query(
        default=10,
        ge=1,
        le=100
    )
):
    """
    Get recent investigation history.
    """

    try:
        investigations = history_service.get_history(
            limit=limit
        )

        return {
            "success": True,
            "investigations": investigations,
            "count": len(investigations)
        }

    except Exception as e:
        logger.error(
            f"Failed to get investigation history: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/history/{investigation_id}")
async def get_single_investigation(
    investigation_id: str
):
    """
    Get one investigation from history.
    """

    try:
        investigation = (
            history_service.get_investigation(
                investigation_id
            )
        )

        if not investigation:
            raise HTTPException(
                status_code=404,
                detail="Investigation not found"
            )

        return {
            "success": True,
            "investigation": investigation
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Failed to get investigation: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/quick")
async def quick_investigate(
    namespace: str = "default",
    enable_ai: bool = True
):
    """
    Run a quick investigation.

    Note:
    The investigation service method is asynchronous,
    so it is awaited here.
    """

    original_ai_setting = investigation_service.enable_ai

    try:
        logger.info(
            f"Received quick investigation request: "
            f"namespace={namespace}, AI={enable_ai}"
        )

        investigation_service.enable_ai = enable_ai

        result = await investigation_service.investigate(
            namespace=namespace,
            collect_logs=False,
            max_log_lines=50
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get(
                    "error",
                    "Quick investigation failed"
                )
            )

        diagnosis = result.get("diagnosis")

        if diagnosis:
            try:
                history_service.save_investigation(
                    investigation_id=result.get(
                        "investigation_id",
                        "unknown"
                    ),
                    cluster=os.getenv(
                        "CURRENT_CLUSTER",
                        "current-context"
                    ),
                    namespace=namespace,
                    diagnosis=diagnosis,
                    status="completed"
                )
            except Exception as history_error:
                logger.error(
                    f"Failed to save quick investigation: "
                    f"{history_error}"
                )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error in quick investigation endpoint: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        investigation_service.enable_ai = (
            original_ai_setting
        )


@router.post("/targeted")
async def investigate_targeted(
    request: TargetedInvestigationRequest
):
    """
    Run a targeted investigation on a specific resource.
    """

    original_ai_setting = investigation_service.enable_ai

    try:
        logger.info(
            f"Received targeted investigation request: "
            f"{request.resource_type}/"
            f"{request.resource_name} "
            f"in {request.namespace}, "
            f"AI={request.enable_ai}"
        )

        investigation_service.enable_ai = request.enable_ai

        result = investigation_service.targeted_investigation(
            resource_name=request.resource_name,
            resource_type=request.resource_type,
            namespace=request.namespace
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get(
                    "error",
                    "Targeted investigation failed"
                )
            )

        diagnosis = result.get("diagnosis")

        if diagnosis:
            try:
                history_service.save_investigation(
                    investigation_id=(
                        f"targeted_"
                        f"{request.resource_type}_"
                        f"{request.resource_name}"
                    ),
                    cluster=os.getenv(
                        "CURRENT_CLUSTER",
                        "current-context"
                    ),
                    namespace=request.namespace,
                    diagnosis=diagnosis,
                    status="completed"
                )
            except Exception as history_error:
                logger.error(
                    f"Failed to save targeted history: "
                    f"{history_error}"
                )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error in targeted investigation endpoint: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        investigation_service.enable_ai = (
            original_ai_setting
        )


@router.get("/health")
async def investigation_health():
    """
    Health check for investigation service.
    """

    try:
        ai_health = (
            investigation_service.ai_agent.health_check()
            if investigation_service.ai_agent
            else {"ai_agent": "disabled"}
        )

        return {
            "status": "healthy",
            "service": "investigation-service",
            "components": [
                "kubectl-executor",
                "pod-inspector",
                "logs-collector",
                "events-analyzer",
                "deployment-inspector",
                "network-inspector",
                "history-service"
            ],
            "ai": ai_health
        }

    except Exception as e:
        logger.error(
            f"Investigation health check failed: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )