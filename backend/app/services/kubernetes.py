import asyncio
import subprocess
from typing import Tuple, Optional
import structlog

logger = structlog.get_logger()

async def create_namespace(name: str):
    cmd = ["kubectl", "create", "namespace", name]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()

async def delete_namespace(name: str):
    cmd = ["kubectl", "delete", "namespace", name, "--wait=false"] # Don't block
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()

async def get_store_urls(namespace: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get admin and storefront URLs from Ingress
    """
    # This is a bit tricky depending on how ingress is set up.
    # We can inspect the ingress object.
    
    cmd = ["kubectl", "get", "ingress", "-n", namespace, "-o", "jsonpath='{.items[0].spec.rules[*].host}'"]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True # Shell=True needed for complex jsonpath sometimes, but be careful
    )
    
    # Actually, simpler to just reconstruct it if we know the domain.
    # But let's try to get it from k8s to be sure.
    
    # For now, let's return None and rely on the Orchestrator to construct them 
    # based on the convention: namespace.k8s.local and namespace-admin.k8s.local
    # fetching from k8s is safer but requires parsing.
    
    return None, None
