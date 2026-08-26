import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from utils import logger
from utils.runtime_paths import configure_runtime_paths, get_runtime_paths

VENV_NAME = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
REQUIREMENTS_STATE_FILE = ".requirements.sha256"


def configure_initial_runtime_paths(project_root: str | Path):
    paths = configure_runtime_paths(project_root=project_root, work_root=project_root)
    configure_native_runtime_paths(paths.project_root)
    return paths


def configure_native_runtime_paths(project_root: str | Path) -> None:
    project_root = Path(project_root).resolve()
    native_dirs = [
        project_root / "runtimes" / "win-x64" / "native",
        project_root / "libs",
    ]
    existing_dirs = [path for path in native_dirs if path.exists()]
    if not existing_dirs:
        return

    os.environ["PATH"] = os.pathsep.join(
        [str(path) for path in existing_dirs] + [os.environ.get("PATH", "")]
    )
    if hasattr(os, "add_dll_directory"):
        for path in existing_dirs:
            os.add_dll_directory(str(path))


def _venv_dir(project_root: Path) -> Path:
    return project_root / VENV_NAME


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python3"


def _is_running_in_project_venv(venv_dir: Path) -> bool:
    try:
        return Path(sys.prefix).resolve() == venv_dir.resolve()
    except Exception:
        return False


def _run_command(cmd: list[str], cwd: Path, operation: str) -> bool:
    logger.info(f"{operation}: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        logger.error(f"{operation} failed: {exc}")
        return False

    if process.stdout:
        for line in process.stdout:
            line = line.rstrip()
            if line:
                logger.debug(line)

    return_code = process.wait()
    if return_code != 0:
        logger.error(f"{operation} failed with exit code {return_code}")
        return False
    return True


def _run(cmd: list[str], cwd: Path, operation: str) -> None:
    if not _run_command(cmd, cwd, operation):
        raise SystemExit(1)


def _read_config(config_name: str, default_config: dict) -> dict:
    config_dir = get_runtime_paths().config_dir
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / f"{config_name}.json"

    if not config_path.exists():
        try:
            config_path.write_text(
                json.dumps(default_config, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            logger.debug(f"Unable to write {config_path}, using defaults")
        return default_config

    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception(f"Unable to read {config_path}, using defaults")
        return default_config


def read_pip_config() -> dict:
    return _read_config(
        "pip_config",
        {
            "enable_pip_install": True,
            "mirror": "https://pypi.tuna.tsinghua.edu.cn/simple",
            "backup_mirror": "https://mirrors.ustc.edu.cn/pypi/simple",
        },
    )


def read_hot_update_config() -> dict:
    return _read_config("hot_update", {"enable_hot_update": False})


def read_interface_version(interface_file_name: str = "interface.json") -> str:
    paths = get_runtime_paths()
    root_interface_path = paths.project_root / interface_file_name
    assets_interface_path = paths.assets_dir / interface_file_name

    if root_interface_path.exists():
        target_path = root_interface_path
    elif assets_interface_path.exists():
        return "DEBUG"
    else:
        logger.warning("interface.json was not found")
        return "unknown"

    try:
        return json.loads(target_path.read_text(encoding="utf-8")).get(
            "version", "unknown"
        )
    except Exception:
        logger.exception(f"Unable to read interface version from {target_path}")
        return "unknown"


def is_dev_mode() -> bool:
    paths = get_runtime_paths()
    return not paths.root_interface_file.exists() and paths.assets_interface_file.exists()


def switch_to_dev_work_root(project_root: str | Path):
    paths = configure_runtime_paths(
        project_root=project_root,
        work_root=get_runtime_paths().assets_dir,
    )
    os.chdir(paths.work_root)
    logger.info(f"set cwd: {os.getcwd()}")
    return paths


def _requirements_hash(requirements_path: Path) -> str:
    digest = hashlib.sha256()
    with open(requirements_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _state_file(venv_dir: Path) -> Path:
    return venv_dir / REQUIREMENTS_STATE_FILE


def _requirements_are_current(venv_dir: Path, requirements_path: Path) -> bool:
    state_path = _state_file(venv_dir)
    if not state_path.exists():
        return False
    try:
        return state_path.read_text(encoding="utf-8").strip() == _requirements_hash(
            requirements_path
        )
    except Exception:
        return False


def _write_requirements_state(venv_dir: Path, requirements_path: Path) -> None:
    _state_file(venv_dir).write_text(
        _requirements_hash(requirements_path), encoding="utf-8"
    )


def _can_import_required_dependencies(python_executable: Path, project_root: Path) -> bool:
    result = subprocess.run(
        [
            str(python_executable),
            "-c",
            "import maa, loguru, PIL, pytz, requests",
        ],
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _ensure_pip(python_executable: Path, project_root: Path) -> None:
    result = subprocess.run(
        [str(python_executable), "-m", "pip", "--version"],
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0:
        return
    _run(
        [str(python_executable), "-m", "ensurepip", "--upgrade"],
        project_root,
        "ensure pip",
    )


def find_local_wheels_dir() -> Path | None:
    deps_dir = get_runtime_paths().deps_dir
    if deps_dir.exists() and any(deps_dir.glob("*.whl")):
        return deps_dir
    return None


def _install_requirements(
    python_executable: Path,
    project_root: Path,
    requirements_path: Path,
    pip_config: dict | None = None,
) -> None:
    _ensure_pip(python_executable, project_root)

    base_cmd = [
        str(python_executable),
        "-m",
        "pip",
        "install",
        "-U",
        "-r",
        str(requirements_path),
        "--no-warn-script-location",
    ]
    if not sys.platform.startswith("win"):
        base_cmd.append("--break-system-packages")

    wheels_dir = find_local_wheels_dir()
    if wheels_dir:
        local_cmd = [*base_cmd, "--find-links", str(wheels_dir), "--no-index"]
        if _run_command(local_cmd, project_root, "install Python requirements from deps"):
            return
        logger.warning("Local wheel install failed, falling back to online install")

    pip_config = pip_config or {}
    primary_mirror = pip_config.get("mirror", "")
    backup_mirror = pip_config.get("backup_mirror", "")
    online_cmd = [*base_cmd]
    if primary_mirror:
        online_cmd.extend(["-i", primary_mirror])
    if backup_mirror:
        online_cmd.extend(["--extra-index-url", backup_mirror])
    _run(online_cmd, project_root, "install Python requirements")


def _create_venv(venv_dir: Path, project_root: Path) -> None:
    if venv_dir.exists():
        return
    _run([sys.executable, "-m", "venv", str(venv_dir)], project_root, "create venv")


def _ensure_venv_dependencies(project_root: Path, venv_dir: Path) -> Path:
    python_executable = _venv_python(venv_dir)
    if not python_executable.exists() and not sys.platform.startswith("win"):
        python_executable = venv_dir / "bin" / "python"
    if not python_executable.exists():
        logger.error(f"Python executable not found in venv: {python_executable}")
        raise SystemExit(1)

    requirements_path = project_root / REQUIREMENTS_FILE
    if not requirements_path.exists():
        logger.error(f"Missing {REQUIREMENTS_FILE} in project root")
        raise SystemExit(1)

    if _requirements_are_current(
        venv_dir, requirements_path
    ) and _can_import_required_dependencies(python_executable, project_root):
        return python_executable

    _install_requirements(
        python_executable,
        project_root,
        requirements_path,
        pip_config=read_pip_config(),
    )
    _write_requirements_state(venv_dir, requirements_path)
    return python_executable


def ensure_venv_and_relaunch_if_needed(
    project_root: str | Path, current_file_path: str | Path
) -> None:
    project_root = Path(project_root).resolve()
    current_file_path = Path(current_file_path).resolve()
    venv_dir = _venv_dir(project_root)

    if _is_running_in_project_venv(venv_dir):
        return

    _create_venv(venv_dir, project_root)
    python_executable = _ensure_venv_dependencies(project_root, venv_dir)

    cmd = [str(python_executable), str(current_file_path), *sys.argv[1:]]
    logger.info("Relaunching Agent in project venv")
    result = subprocess.run(cmd, cwd=project_root, env=os.environ.copy(), check=False)
    raise SystemExit(result.returncode)


def check_and_install_dependencies() -> None:
    paths = get_runtime_paths()
    if _can_import_required_dependencies(Path(sys.executable), paths.project_root):
        logger.debug("Python requirements are already importable")
        return

    pip_config = read_pip_config()
    if not pip_config.get("enable_pip_install", True):
        logger.info("Pip dependency installation is disabled")
        return
    _install_requirements(
        Path(sys.executable),
        paths.project_root,
        paths.requirements_file,
        pip_config=pip_config,
    )
