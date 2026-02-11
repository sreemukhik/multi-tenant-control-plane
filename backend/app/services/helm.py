import subprocess
import asyncio
from typing import Dict, Any, Tuple
import structlog

logger = structlog.get_logger()

class HelmInstallError(Exception):
    pass

async def helm_install(
    release_name: str,
    chart_path: str,
    namespace: str,
    values: Dict[str, Any],
    timeout: str = "10m",
    wait: bool = True,
    create_namespace: bool = True
) -> subprocess.CompletedProcess:
    """
    Install Helm chart using CLI
    """
    cmd = [
        "helm", "upgrade", "--install", release_name, chart_path,
        "--namespace", namespace,
        "--timeout", timeout,
    ]
    
    if create_namespace:
        cmd.append("--create-namespace")
    
    if wait:
        cmd.append("--wait")
    
    # Add values
    for key, val in values.items():
        cmd.extend(["--set", f"{key}={val}"])
    
    logger.info("helm_install_started", release_name=release_name, cmd=" ".join(cmd))
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        logger.error("helm_install_failed", stderr=stderr.decode())
        raise HelmInstallError(stderr.decode())
        
    logger.info("helm_install_success", stdout=stdout.decode())

    return subprocess.CompletedProcess(
        args=cmd,
        returncode=process.returncode,
        stdout=stdout.decode(),
        stderr=stderr.decode()
    )

async def helm_uninstall(release_name: str, namespace: str) -> None:
    """
    Uninstall Helm release
    """
    cmd = ["helm", "uninstall", release_name, "--namespace", namespace]
    
    logger.info("helm_uninstall_started", release_name=release_name)
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        logger.error("helm_uninstall_failed", stderr=stderr.decode())
        # We might not want to raise here depending on cleanup logic
    
    logger.info("helm_uninstall_success")
