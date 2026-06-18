from pathlib import Path
from typing import List

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

def find_batch_files(input_dir: str = "input_batch") -> List[Path]:
    folder = Path(input_dir)

    if not folder.exists():
        raise FileNotFoundError(f"Папка не найдена: {folder}")

    files = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        raise FileNotFoundError(
            f"В папке {folder} нет файлов .pdf или .docx"
        )

    files.sort(key=lambda x: x.name.lower())
    return files