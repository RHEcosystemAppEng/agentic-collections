from __future__ import annotations

from pathlib import Path


PACKS = [
    "rh-sre",
    "rh-developer",
    "ocp-admin",
    "rh-virt",
    "rh-ai-engineer",
    "rh-automation",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def pack_readmes(root: Path) -> dict[str, Path]:
    return {pack: root / pack / "README.md" for pack in PACKS}


def skill_files_for_pack(root: Path, pack: str) -> list[Path]:
    skills_dir = root / pack / "skills"
    if not skills_dir.exists():
        return []
    return sorted(skills_dir.glob("*/SKILL.md"))


def all_skill_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for pack in PACKS:
        files.extend(skill_files_for_pack(root, pack))
    return files

