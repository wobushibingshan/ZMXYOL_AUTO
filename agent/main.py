import os
import sys
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parent
_AGENT_PATH = str(_AGENT_DIR)
if _AGENT_PATH not in sys.path:
    sys.path.insert(0, _AGENT_PATH)

from agent_runtime import run_agent
from bootstrap import (
    check_and_install_dependencies,
    configure_initial_runtime_paths,
    ensure_venv_and_relaunch_if_needed,
    is_dev_mode,
    switch_to_dev_work_root,
)
from utils import logger


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass


def _configure_project_root() -> tuple[Path, Path]:
    current_file = Path(__file__).resolve()
    agent_dir = current_file.parent
    project_root = agent_dir.parent

    if Path.cwd().resolve() != project_root:
        os.chdir(project_root)

    agent_path = str(agent_dir)
    if agent_path not in sys.path:
        sys.path.insert(0, agent_path)

    return current_file, project_root


def main() -> int:
    _configure_stdio()
    current_file, project_root = _configure_project_root()
    configure_initial_runtime_paths(project_root)

    dev_mode = is_dev_mode()
    logger.debug(f"dev_mode={dev_mode}")
    if dev_mode:
        ensure_venv_and_relaunch_if_needed(project_root, current_file)
        switch_to_dev_work_root(project_root)

    check_and_install_dependencies()
    return run_agent(project_root_dir=str(project_root), is_dev_mode=dev_mode)


if __name__ == "__main__":
    raise SystemExit(main())
