import os
import sys

from utils import logger


def _format_env_value(value: str, limit: int = 300) -> str:
    if not value:
        return "<empty>"
    if len(value) <= limit:
        return value
    return f"{value[:limit]}...(truncated, total={len(value)})"


def log_pi_environment() -> None:
    pi_env_keys = [
        "PI_INTERFACE_VERSION",
        "PI_CLIENT_NAME",
        "PI_CLIENT_VERSION",
        "PI_CLIENT_LANGUAGE",
        "PI_CLIENT_MAAFW_VERSION",
        "PI_VERSION",
        "PI_CONTROLLER",
        "PI_RESOURCE",
    ]

    logger.debug("PI environment snapshot:")
    for key in pi_env_keys:
        logger.debug(f"{key}={_format_env_value(os.getenv(key, ''))}")


def run_agent(project_root_dir: str, is_dev_mode: bool = False) -> int:
    from maa.agent.agent_server import AgentServer
    from maa.tasker import Tasker
    from maa.toolkit import Toolkit

    import custom

    Toolkit.init_option("./")
    custom.register_all()
    Tasker.set_log_dir("./debug")

    if len(sys.argv) < 2:
        logger.error("Missing required socket_id argument")
        print("Usage: python agent/main.py <socket_id>")
        return 1

    socket_id = sys.argv[-1]
    logger.debug(f"project_root={project_root_dir}")
    logger.debug(f"is_dev_mode={is_dev_mode}")
    logger.debug(f"socket_id={socket_id}")
    log_pi_environment()

    started = False
    try:
        AgentServer.start_up(socket_id)
        started = True
        logger.info("AgentServer started")
        AgentServer.join()
        return 0
    finally:
        if started:
            AgentServer.shut_down()
            logger.info("AgentServer shut down")
