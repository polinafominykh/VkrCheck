from pathlib import Path
import shutil
import tempfile
import uuid

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from core.orchestrator import VKROrchestrator
from reporting.json_report import pipeline_report_to_dict, save_pipeline_report_json
from reporting.pdf_report import save_pipeline_report_pdf
app = FastAPI(title="VKRGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui_web"
OUTPUT_DIR = BASE_DIR / "output_web"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

orchestrator = VKROrchestrator(
    formal_criteria_path="criteria/formal_criteria.yaml",
    structure_criteria_path="criteria/structure_criteria.yaml",
    semantic_criteria_path="criteria/semantic_criteria.yaml",
    degree="master",
)

@app.get("/")
def root():
    return FileResponse(UI_DIR / "index.html")

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    formal: bool = Form(False),
    structure: bool = Form(False),
    semantic: bool = Form(False),
):
    enabled_agents = []

    if formal:
        enabled_agents.append("formal")
    if structure:
        enabled_agents.append("structure")
    if semantic:
        enabled_agents.append("semantic")

    if not enabled_agents:
        return {
            "ok": False,
            "message": "Не выбран ни один агент",
        }

    suffix = Path(file.filename).suffix.lower()
    temp_dir = Path(tempfile.mkdtemp())
    input_path = temp_dir / f"uploaded{suffix}"

    try:
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)

        report = orchestrator.run(
            file_path=str(input_path),
            enabled_agents=enabled_agents,
        )

        job_id = str(uuid.uuid4())[:8]
        json_path = OUTPUT_DIR / f"{job_id}_report.json"
        pdf_path = OUTPUT_DIR / f"{job_id}_report.pdf"

        save_pipeline_report_json(report, str(json_path))
        save_pipeline_report_pdf(report, str(pdf_path))

        data = pipeline_report_to_dict(report)
        data["ok"] = True
        data["job_id"] = job_id
        data["enabled_agents"] = enabled_agents
        data["downloads"] = {
            "json": f"/download/json/{job_id}",
            "pdf": f"/download/pdf/{job_id}",
        }

        return data

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/download/json/{job_id}")
def download_json(job_id: str):
    path = OUTPUT_DIR / f"{job_id}_report.json"
    return FileResponse(path, filename=path.name, media_type="application/json")

@app.get("/download/pdf/{job_id}")
def download_pdf(job_id: str):
    path = OUTPUT_DIR / f"{job_id}_report.pdf"
    return FileResponse(path, filename=path.name, media_type="application/pdf")