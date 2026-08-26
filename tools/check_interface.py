#!/usr/bin/env python3
"""Validate interface imports, pipeline entries, and daily presets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
INTERFACE_FILE = ASSETS / "interface.json"
PIPELINE_DIR = ASSETS / "resource" / "base" / "pipeline"
TASK_DIR = ASSETS / "resource" / "tasks"

DAILY_PRESET_NAMES = ("一键日常", "游戏内日常", "仅启动到村庄")
REQUIRED_DAILY_TASKS = (
    "启动游戏",
    "冰霜遗迹",
    "一键碾压",
    "仙盟建设",
    "关卡扫荡",
    "联盟",
    "法相挖宝",
    "关闭游戏",
)
KNOWN_GAME_PACKAGES = {
    "腾讯应用宝": "com.tencent.tmgp.zmxyol",
    "小米": "com.zmxyol.union.mi",
    "UC九游": "com.zmxyol.union.uc",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_json_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*.json") if path.is_file())


def merge_imported(interface: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "task": list(interface.get("task") or []),
        "option": dict(interface.get("option") or {}),
        "preset": list(interface.get("preset") or []),
        "group": list(interface.get("group") or []),
        "global_option": list(interface.get("global_option") or []),
    }
    interface_dir = INTERFACE_FILE.parent
    for relative in interface.get("import") or []:
        imported = load_json(interface_dir / relative)
        merged["task"].extend(imported.get("task") or [])
        merged["option"].update(imported.get("option") or {})
        merged["preset"].extend(imported.get("preset") or [])
        merged["group"].extend(imported.get("group") or [])
        merged["global_option"].extend(imported.get("global_option") or [])
    return merged


def collect_pipeline_nodes() -> set[str]:
    nodes: set[str] = set()
    for path in iter_json_files(PIPELINE_DIR):
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        for key in data:
            if not str(key).startswith("$"):
                nodes.add(key)
    return nodes


def collect_image_references(node: dict[str, Any]) -> list[str]:
    templates: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            template = value.get("template")
            if isinstance(template, str):
                templates.append(template)
            elif isinstance(template, list):
                templates.extend(item for item in template if isinstance(item, str))
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(node)
    return templates


def image_exists(template: str) -> bool:
    return (ASSETS / "resource" / "base" / "image" / template).is_file()


def validate() -> list[str]:
    errors: list[str] = []
    interface = load_json(INTERFACE_FILE)
    merged = merge_imported(interface)
    pipeline_nodes = collect_pipeline_nodes()

    tasks = {task["name"]: task for task in merged["task"] if "name" in task}
    options = merged["option"]
    groups = {group["name"] for group in merged["group"] if "name" in group}
    presets = {preset["name"]: preset for preset in merged["preset"] if "name" in preset}

    for relative in interface.get("import") or []:
        path = INTERFACE_FILE.parent / relative
        if not path.is_file():
            errors.append(f"missing import file: {relative}")

    for task_name, task in tasks.items():
        entry = task.get("entry")
        if not entry:
            errors.append(f"task {task_name!r} is missing entry")
        elif entry not in pipeline_nodes:
            errors.append(f"task {task_name!r} entry {entry!r} is not a pipeline node")

        for option_name in task.get("option") or []:
            if option_name not in options:
                errors.append(f"task {task_name!r} references unknown option {option_name!r}")

        for group_name in task.get("group") or []:
            if group_name not in groups:
                errors.append(f"task {task_name!r} references unknown group {group_name!r}")

    for option_name in merged["global_option"]:
        if option_name not in options:
            errors.append(f"global_option references unknown option {option_name!r}")

    for preset_name in DAILY_PRESET_NAMES:
        if preset_name not in presets:
            errors.append(f"missing daily preset {preset_name!r}")

    one_click = presets.get("一键日常") or {}
    enabled = {
        item["name"]
        for item in one_click.get("task") or []
        if item.get("enabled", True)
    }
    for task_name in REQUIRED_DAILY_TASKS:
        if task_name not in tasks:
            errors.append(f"missing required daily task {task_name!r}")
        if task_name not in enabled:
            errors.append(f"preset 一键日常 does not enable {task_name!r}")

    in_game = presets.get("游戏内日常") or {}
    in_game_enabled = {
        item["name"]: item.get("enabled", True)
        for item in in_game.get("task") or []
    }
    if in_game_enabled.get("启动游戏"):
        errors.append("preset 游戏内日常 should not enable 启动游戏")
    if in_game_enabled.get("关闭游戏"):
        errors.append("preset 游戏内日常 should not enable 关闭游戏")

    for preset in merged["preset"]:
        for item in preset.get("task") or []:
            task_name = item.get("name")
            if task_name not in tasks:
                errors.append(
                    f"preset {preset.get('name')!r} references unknown task {task_name!r}"
                )

    channel = options.get("游戏渠道") or {}
    cases = {case["name"]: case for case in channel.get("cases") or [] if "name" in case}
    for case_name, package in KNOWN_GAME_PACKAGES.items():
        case = cases.get(case_name)
        if case is None:
            errors.append(f"missing game channel case {case_name!r}")
            continue
        override = case.get("pipeline_override") or {}
        for node_name in ("启动游戏", "关闭游戏"):
            actual = (
                ((override.get(node_name) or {}).get("action") or {}).get("param") or {}
            ).get("package")
            if actual != package:
                errors.append(
                    f"channel {case_name!r} node {node_name!r} package is {actual!r}, expected {package!r}"
                )

    for path in iter_json_files(PIPELINE_DIR):
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        for node_name, node in data.items():
            if str(node_name).startswith("$") or not isinstance(node, dict):
                continue
            for template in collect_image_references(node):
                if not image_exists(template):
                    errors.append(
                        f"pipeline node {node_name!r} in {path.relative_to(ROOT)} "
                        f"references missing image {template!r}"
                    )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Interface validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Interface validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
