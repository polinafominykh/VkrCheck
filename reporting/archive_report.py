from pathlib import Path
import shutil
import zipfile

def prepare_batch_output(output_dir: str = "output_batch") -> dict:
    root = Path(output_dir)
    works_dir = root / "works"
    reports_dir = root / "reports"

    works_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    return {
        "root": root,
        "works": works_dir,
        "reports": reports_dir,
        "zip": root / "vkr_reports_archive.zip",
    }

def copy_work_to_output(source_file: Path, works_dir: Path) -> Path:
    target = works_dir / source_file.name
    shutil.copy2(source_file, target)
    return target

def build_report_pdf_path(source_file: Path, reports_dir: Path) -> Path:
    return reports_dir / f"{source_file.stem}_report.pdf"

def build_report_json_path(source_file: Path, reports_dir: Path) -> Path:
    return reports_dir / f"{source_file.stem}_report.json"

def make_zip_archive(root_dir: Path, zip_path: Path) -> Path:
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in root_dir.rglob("*"):
            if file_path.is_file() and file_path != zip_path:
                arcname = file_path.relative_to(root_dir)
                zf.write(file_path, arcname)

    return zip_path