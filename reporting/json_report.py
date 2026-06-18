import json
from pathlib import Path
from typing import Any, Dict
from core.schemas import PipelineReport

def _result_to_dict(result) -> Dict[str, Any]:
    return {
        "criterion_id": result.criterion_id,
        "criterion_name": result.criterion_name,
        "status": result.status,
        "message": result.message,
        "evidence": result.evidence,
        "recommendations": result.recommendations,
    }

def pipeline_report_to_dict(report: PipelineReport) -> Dict[str, Any]:
    return {
        "summary": {
            "passed": report.passed,
            "warned": report.warned,
            "failed": report.failed,
            "total": len(report.all_results),
        },
        "chapters": list(report.chapters.keys()),
        "normalized_sections": list(report.normalized_sections.keys()),
        "formal_results": [_result_to_dict(r) for r in report.formal_results],
        "semantic_results": [_result_to_dict(r) for r in report.semantic_results],
        "all_results": [_result_to_dict(r) for r in report.all_results],
    }

def save_pipeline_report_json(report: PipelineReport, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = pipeline_report_to_dict(report)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return str(path)