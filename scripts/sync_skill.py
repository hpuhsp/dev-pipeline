#!/usr/bin/env python3
"""Build and verify the dev-pipeline package and configured local skill copy."""

from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import shutil
import tempfile
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / ".claude" / "skills" / "dev-pipeline"
DEFAULT_PACKAGE = ROOT / "dev-pipeline.skill"
DEFAULT_INSTALLED = (
    pathlib.Path(os.environ.get("USERPROFILE", pathlib.Path.home()))
    / ".agents"
    / "skills"
    / "dev-pipeline"
)


def source_files(source: pathlib.Path) -> list[pathlib.Path]:
    return sorted(path for path in source.rglob("*") if path.is_file())


def package_members(source: pathlib.Path) -> list[str]:
    return sorted(path.relative_to(source).as_posix() for path in source_files(source))


def file_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_package(source: pathlib.Path, package: pathlib.Path) -> None:
    package.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{package.stem}-", suffix=".skill", dir=package.parent
    )
    os.close(descriptor)
    temporary = pathlib.Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path in source_files(source):
                archive.write(path, path.relative_to(source).as_posix())
        os.replace(temporary, package)
    finally:
        temporary.unlink(missing_ok=True)


def validate_package(source: pathlib.Path, package: pathlib.Path) -> None:
    if not package.is_file():
        raise ValueError(f"package missing: {package}")
    expected = package_members(source)
    with zipfile.ZipFile(package) as archive:
        actual = sorted(entry.filename for entry in archive.infolist() if not entry.is_dir())
        if actual != expected:
            raise ValueError("package contents do not match the source skill")
        for path in source_files(source):
            member = path.relative_to(source).as_posix()
            if archive.read(member) != path.read_bytes():
                raise ValueError(f"package content differs for {member}")


def sync_installed(source: pathlib.Path, installed: pathlib.Path) -> None:
    for path in source_files(source):
        destination = installed / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def validate_installed(source: pathlib.Path, installed: pathlib.Path) -> None:
    if not installed.is_dir():
        raise ValueError(f"configured skill missing: {installed}")
    for path in source_files(source):
        destination = installed / path.relative_to(source)
        if not destination.is_file():
            raise ValueError(f"configured skill missing file: {destination}")
        if file_digest(destination) != file_digest(path):
            raise ValueError(f"configured skill content differs for {path.relative_to(source)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=pathlib.Path, default=DEFAULT_SOURCE)
    parser.add_argument("--package", type=pathlib.Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--installed", type=pathlib.Path, default=DEFAULT_INSTALLED)
    parser.add_argument("--skip-installed", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        validate_package(args.source, args.package)
        if not args.skip_installed:
            validate_installed(args.source, args.installed)
        print("Skill package and configured copy are synchronized.")
        return 0

    build_package(args.source, args.package)
    validate_package(args.source, args.package)
    if not args.skip_installed:
        sync_installed(args.source, args.installed)
        validate_installed(args.source, args.installed)
    print(f"Built {args.package}")
    if not args.skip_installed:
        print(f"Synchronized {args.installed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
