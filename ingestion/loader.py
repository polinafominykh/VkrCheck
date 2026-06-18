from pathlib import Path
from typing import List, Union
from ingestion.load_pdf import load_pdf
from ingestion.load_docx import load_docx

def load_document(file_path: Union[str, Path]) -> List[str]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(path)

    if suffix == ".docx":
        return load_docx(path)

    raise ValueError(f"Неподдерживаемый формат файла: {suffix}")