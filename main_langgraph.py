from core.langgraph_orchestrator import VKRLangGraphOrchestrator
from reporting.json_report import save_pipeline_report_json
from reporting.pdf_report import save_pipeline_report_pdf

def main():
    file_path = "input/sample.pdf"

    orchestrator = VKRLangGraphOrchestrator(
        formal_criteria_path="criteria/formal_criteria.yaml",
        structure_criteria_path="criteria/structure_criteria.yaml",
        semantic_criteria_path="criteria/semantic_criteria.yaml",
        degree="master",
    )

    report = orchestrator.run(file_path)

    print("\n=== FORMAL + STRUCTURE REPORT ===")
    for result in report.formal_results:
        print(f"[{result.status.upper()}] {result.criterion_name}: {result.message}")

    print("\n=== SEMANTIC REPORT ===")
    for result in report.semantic_results:
        print(f"[{result.status.upper()}] {result.criterion_name}: {result.message}")

    print("\n=== SUMMARY ===")
    print("PASS:", report.passed)
    print("WARN:", report.warned)
    print("FAIL:", report.failed)

    json_path = save_pipeline_report_json(report, "output/report_langgraph.json")
    pdf_path = save_pipeline_report_pdf(report, "output/report_langgraph.pdf")

    print("\nJSON REPORT SAVED TO:", json_path)
    print("PDF REPORT SAVED TO:", pdf_path)

if __name__ == "__main__":
    main()