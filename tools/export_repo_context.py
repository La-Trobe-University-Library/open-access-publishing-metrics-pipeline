from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import pathspec

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_IGNORES = [
    ".git/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    "node_modules/",
    "dist/",
    "build/",
    ".idea/",
    ".vscode/",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dll",
    "*.exe",
    "*.bin",
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.gif",
    "*.webp",
    "*.pdf",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.sqlite",
    "*.db",
    "*.parquet",
]

ALLOWED_EXTENSIONS = {
    ".py",
    ".sql",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".ps1",
    ".env",
    ".xml",
    ".csv",
}

ALLOWED_FILENAMES = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
    ".gitignore",
    "Makefile",
}

MAX_FILE_BYTES = 500_000
DEFAULT_MAX_CHARS_PER_PART = 800_000


def load_gitignore_spec(repo_root: Path) -> pathspec.PathSpec:
    patterns: List[str] = []
    gitignore = repo_root / ".gitignore"

    if gitignore.exists():
        patterns.extend(gitignore.read_text(encoding="utf-8").splitlines())

    patterns.extend(DEFAULT_IGNORES)

    return pathspec.PathSpec.from_lines(
        pathspec.patterns.GitWildMatchPattern,
        patterns,
    )


def is_ignored(path: Path, repo_root: Path, spec: pathspec.PathSpec) -> bool:
    rel = path.relative_to(repo_root).as_posix()
    if path.is_dir():
        rel += "/"
    return spec.match_file(rel)


def is_probably_text(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            sample = f.read(4096)
        sample.decode("utf-8")
        return True
    except Exception:
        return False


def is_allowed_file(path: Path) -> bool:
    return path.suffix.lower() in ALLOWED_EXTENSIONS or path.name in ALLOWED_FILENAMES


def iter_repo_files(repo_root: Path, spec: pathspec.PathSpec) -> Iterable[Path]:
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        if is_ignored(path, repo_root, spec):
            continue
        if not is_allowed_file(path):
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            continue
        if not is_probably_text(path):
            continue
        yield path


def language_from_path(path: Path) -> str:
    if path.name == "Dockerfile":
        return "dockerfile"
    if path.name in {"docker-compose.yml", "docker-compose.yaml"}:
        return "yaml"

    mapping = {
        ".py": "python",
        ".sql": "sql",
        ".md": "markdown",
        ".txt": "text",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".sh": "bash",
        ".ps1": "powershell",
        ".env": "bash",
        ".xml": "xml",
        ".csv": "csv",
    }
    return mapping.get(path.suffix.lower(), "text")


def build_file_section(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).as_posix()
    lang = language_from_path(path)

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="replace")

    section = []
    section.append("\n---\n")
    section.append(f"\n## FILE: `{rel}`\n\n")
    section.append(f"```{lang}\n")
    section.append(content)
    if not content.endswith("\n"):
        section.append("\n")
    section.append("```\n")

    return "".join(section)


def build_header(repo_root: Path, files: List[Path], part_no: int, total_parts: int) -> str:
    header = []
    header.append("# Repository Context Export\n\n")
    header.append(f"Root: `{repo_root}`\n\n")
    header.append(f"Part: {part_no} of {total_parts}\n\n")
    header.append(f"Total included files in export set: {len(files)}\n\n")
    header.append(
        "This file is part of a multi-part export intended for LLM context. "
        "Each section below contains one repository file.\n\n"
    )
    return "".join(header)


def split_sections_into_parts(
    sections: List[tuple[str, str]],
    max_chars_per_part: int,
) -> List[List[tuple[str, str]]]:
    """
    sections is a list of (relative_path, rendered_section).
    """
    parts: List[List[tuple[str, str]]] = []
    current_part: List[tuple[str, str]] = []
    current_size = 0

    for rel_path, section in sections:
        section_size = len(section)

        # If a single file is larger than the threshold, still allow it in its own part.
        if current_part and current_size + section_size > max_chars_per_part:
            parts.append(current_part)
            current_part = []
            current_size = 0

        current_part.append((rel_path, section))
        current_size += section_size

    if current_part:
        parts.append(current_part)

    return parts


def write_parts(
    out_base: Path,
    repo_root: Path,
    all_files: List[Path],
    parts: List[List[tuple[str, str]]],
) -> List[Path]:
    written_files: List[Path] = []

    if len(parts) == 1:
        out_file = out_base.with_suffix(".md") if out_base.suffix == "" else out_base
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(build_header(repo_root, all_files, 1, 1))
            for _, section in parts[0]:
                f.write(section)
        written_files.append(out_file)
        return written_files

    stem = out_base.stem if out_base.suffix else out_base.name
    suffix = out_base.suffix if out_base.suffix else ".md"
    parent = out_base.parent if out_base.parent != Path("") else Path(".")

    total_parts = len(parts)
    width = max(2, len(str(total_parts)))

    for idx, part_sections in enumerate(parts, start=1):
        out_file = parent / f"{stem}_part_{idx:0{width}d}{suffix}"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(build_header(repo_root, all_files, idx, total_parts))
            for _, section in part_sections:
                f.write(section)
        written_files.append(out_file)

    return written_files


def write_index_file(
    out_base: Path,
    repo_root: Path,
    all_files: List[Path],
    parts: List[List[tuple[str, str]]],
    written_files: List[Path],
) -> Path:
    stem = out_base.stem if out_base.suffix else out_base.name
    parent = out_base.parent if out_base.parent != Path("") else Path(".")
    index_file = parent / f"{stem}_index.md"

    with open(index_file, "w", encoding="utf-8") as f:
        f.write("# Repository Export Index\n\n")
        f.write(f"Root: `{repo_root}`\n\n")
        f.write(f"Total files included: {len(all_files)}\n\n")
        f.write(f"Total output parts: {len(written_files)}\n\n")

        for part_no, (written_file, part_sections) in enumerate(zip(written_files, parts), start=1):
            f.write(f"## Part {part_no}: `{written_file.name}`\n\n")
            for rel_path, _ in part_sections:
                f.write(f"- `{rel_path}`\n")
            f.write("\n")

    return index_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the repo into one or more LLM-friendly markdown files"
    )
    parser.add_argument(
        "--out",
        default="repo_context.md",
        help="Base output file path. If splitting occurs, files will be named like repo_context_part_01.md",
    )
    parser.add_argument(
        "--max-chars-per-part",
        type=int,
        default=DEFAULT_MAX_CHARS_PER_PART,
        help="Maximum approximate characters per output part",
    )
    args = parser.parse_args()

    spec = load_gitignore_spec(REPO_ROOT)
    files = list(iter_repo_files(REPO_ROOT, spec))

    if not files:
        print("No eligible files found.")
        return

    sections: List[tuple[str, str]] = []
    for path in files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        sections.append((rel, build_file_section(path)))

    parts = split_sections_into_parts(
        sections=sections,
        max_chars_per_part=args.max_chars_per_part,
    )

    SCRIPT_DIR = Path(__file__).resolve().parent
    out_base = SCRIPT_DIR / args.out
    written_files = write_parts(
        out_base=out_base,
        repo_root=REPO_ROOT,
        all_files=files,
        parts=parts,
    )

    index_file = write_index_file(
        out_base=out_base,
        repo_root=REPO_ROOT,
        all_files=files,
        parts=parts,
        written_files=written_files,
    )

    print(f"Included files: {len(files)}")
    print(f"Output parts: {len(written_files)}")
    for file in written_files:
        print(f" - {file.resolve()}")
    print(f"Index file: {index_file.resolve()}")


if __name__ == "__main__":
    main()