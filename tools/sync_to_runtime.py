#!/usr/bin/env python3
"""Sync source assets and Agent into an existing MFA install directory.

This does not rebuild MFAAvalonia.exe. It overwrites resource/, agent/,
requirements.txt and interface.json in the runtime folder, and keeps the
embedded Python path used by the unpacked Windows package.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from configure import configure_ocr_model

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"
AGENT_DIR = ROOT / "agent"
DEFAULT_RUNTIME = Path(r"D:\ZMXY_AUTO\ZMXYOL_AUTO-win-x86_64")
PACKAGED_AGENT = {
    "child_exec": "./python/python.exe",
    "child_args": ["-u", "./agent/main.py"],
}


def _copy_replace(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def sync_to_runtime(dest: Path, version: str | None = None) -> Path:
    dest = dest.resolve()
    exe = dest / "MFAAvalonia.exe"
    if not exe.is_file():
        raise FileNotFoundError(
            f"未找到 {exe}。请确认这是已解压的 Windows 运行目录，"
            "且 MFAAvalonia.exe 还在。"
        )

    configure_ocr_model(ASSETS_DIR)

    interface_src = ASSETS_DIR / "interface.json"
    resource_src = ASSETS_DIR / "resource"
    if not interface_src.is_file() or not resource_src.is_dir() or not AGENT_DIR.is_dir():
        raise FileNotFoundError("仓库缺少 assets/interface.json、assets/resource 或 agent/")

    _copy_replace(resource_src, dest / "resource")
    _copy_replace(AGENT_DIR, dest / "agent")
    shutil.copy2(ROOT / "requirements.txt", dest / "requirements.txt")

    with open(interface_src, encoding="utf-8") as file:
        interface = json.load(file)

    interface["agent"] = dict(PACKAGED_AGENT)
    if version:
        interface["version"] = version

    with open(dest / "interface.json", "w", encoding="utf-8") as file:
        json.dump(interface, file, ensure_ascii=False, indent=4)
        file.write("\n")

    print(f"已同步到 {dest}")
    print("请先关闭 MFAAvalonia.exe，再重新打开该目录下的 exe。")
    return dest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把仓库里的 JSON / 图片 / Python 同步到现有 exe 目录，无需重新打包。"
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_RUNTIME,
        help=f"已解压的 MFA 目录（默认 {DEFAULT_RUNTIME}）",
    )
    parser.add_argument("--version", default=None, help="写入 interface.json 的版本号")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        sync_to_runtime(args.dest, version=args.version)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
