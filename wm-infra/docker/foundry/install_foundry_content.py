#!/usr/bin/env python3

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import requests
import yaml


def install_kind(module: dict) -> str:
    explicit_kind = module.get("_kind")
    if explicit_kind in {"systems", "modules"}:
        return explicit_kind
    raise RuntimeError("Module entry is missing its manifest kind")


def render_url(module: dict) -> str:
    return module["url"].format(**module)


def download_zip(module: dict, destination: Path) -> None:
    auth = None
    if module.get("http_user") and module.get("http_password"):
        auth = (module["http_user"], module["http_password"])

    response = requests.get(render_url(module), stream=True, timeout=120, auth=auth)
    response.raise_for_status()
    with destination.open("wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 64):
            if chunk:
                f.write(chunk)


def discover_content_root(extract_dir: Path) -> Path:
    manifests = list(extract_dir.rglob("module.json")) + list(extract_dir.rglob("system.json"))
    if not manifests:
        raise RuntimeError("Could not find module.json or system.json in archive")
    return manifests[0].parent


def install_module(module: dict, output_dir: Path) -> None:
    kind = install_kind(module)
    module_name = module["name"]
    target_root = output_dir / "Data" / kind

    with tempfile.TemporaryDirectory(prefix=f"{module_name}-") as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / f"{module_name}-{module['version']}.zip"
        extract_path = temp_path / "extract"
        extract_path.mkdir(parents=True, exist_ok=True)

        print(f"Installing {kind}/{module_name}:{module['version']}")
        download_zip(module, zip_path)

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_path)

        content_root = discover_content_root(extract_path)
        target_name = module_name if module.get("rename", False) else content_root.name
        target_path = target_root / target_name
        target_root.mkdir(parents=True, exist_ok=True)

        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.copytree(content_root, target_path)


def load_modules(manifest_path: Path) -> list[dict]:
    data = yaml.safe_load(manifest_path.read_text())
    systems = data.get("foundry_systems", [])
    modules = data.get("foundry_modules", [])
    if not isinstance(systems, list):
        raise RuntimeError("Manifest does not define a valid foundry_systems list")
    if not isinstance(modules, list):
        raise RuntimeError("Manifest does not define a valid foundry_modules list")
    return [*({**entry, "_kind": "systems"} for entry in systems), *({**entry, "_kind": "modules"} for entry in modules)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Foundry systems/modules from manifest")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("modules.yml"),
        help="Path to modules manifest (defaults to docker/foundry/modules.yml)",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output root directory")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "Data" / "modules").mkdir(parents=True, exist_ok=True)
    (args.output / "Data" / "systems").mkdir(parents=True, exist_ok=True)

    try:
        modules = load_modules(args.manifest)
        for module in modules:
            if not module or not module.get("name") or not module.get("version") or not module.get("url"):
                continue
            install_module(module, args.output)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(f"[OK] Foundry content built at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
