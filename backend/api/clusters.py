from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
import os
import sys

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from kubectl.kubeconfig_reader import KubeconfigReader


router = APIRouter(prefix="/clusters", tags=["clusters"])


class SwitchRequest(BaseModel):
    context_name: str


@router.get("/")
async def get_clusters():
    """
    Get available Kubernetes clusters from kubeconfig.
    
    Returns list of clusters with their information.
    """
    try:
        kubeconfig_path = os.getenv("KUBECONFIG_PATH") or os.path.expanduser("~/.kube/config")
        reader = KubeconfigReader(kubeconfig_path=kubeconfig_path)
        
        clusters = reader.get_clusters()
        
        if not clusters:
            return {
                "clusters": [],
                "message": "No clusters found in kubeconfig",
                "kubeconfig_path": kubeconfig_path
            }
        
        return {
            "clusters": clusters,
            "current_context": reader.get_current_context(),
            "kubeconfig_path": kubeconfig_path
        }
        
    except Exception as e:
        logger.error(f"Error getting clusters: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch")
async def switch_cluster(request: SwitchRequest):
    """
    Switch to a different Kubernetes cluster context.
    
    Args:
        request: SwitchRequest with context_name
        
    Returns:
        Success/failure status
    """
    try:
        kubeconfig_path = os.getenv("KUBECONFIG_PATH") or os.path.expanduser("~/.kube/config")
        reader = KubeconfigReader(kubeconfig_path=kubeconfig_path)
        
        success = reader.set_context(request.context_name)
        
        if success:
            return {
                "success": True,
                "message": f"Switched to context: {request.context_name}",
                "current_context": request.context_name
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to switch to context: {request.context_name}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching cluster: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))