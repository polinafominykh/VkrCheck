from pathlib import Path
from typing import List

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

def find_input_file(input_dir: str = "input") -> Path:
    folder = Path(input_dir)

    if not folder.exists():
        raise FileNotFoundError(f"Папка не найдена: {folder}")

    files: List[Path] = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        raise FileNotFoundError(
            f"В папке {folder} нет файлов .pdf или .docx"
        )

    if len(files) > 1:
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return files[0]

    return files[0]


def build_output_paths(source_file: Path, output_dir: str = "output") -> dict:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = source_file.stem

    return {
        "json": out_dir / f"{stem}_report.json",
        "pdf": out_dir / f"{stem}_report.pdf",
    }