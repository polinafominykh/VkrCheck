from core.orchestrator import VKROrchestrator
from core.file_runner import find_input_file, build_output_paths
from reporting.json_report import save_pipeline_report_json
from reporting.pdf_report import save_pipeline_report_pdf

def main():
    source_file = find_input_file("input")
    output_paths = build_output_paths(source_file, "output")

    print("Найден файл:", source_file)

    orchestrator = VKROrchestrator(
        formal_criteria_path="criteria/formal_criteria.yaml",
        structure_criteria_path="criteria/structure_criteria.yaml",
        semantic_criteria_path="criteria/semantic_criteria.yaml",
        degree="master",
    )

    report = orchestrator.run(str(source_file))

    print("\n=== SUMMARY ===")
    print("PASS:", report.passed)
    print("WARN:", report.warned)
    print("FAIL:", report.failed)

    json_path = save_pipeline_report_json(report, str(output_paths["json"]))
    pdf_path = save_pipeline_report_pdf(report, str(output_paths["pdf"]))

    print("\nJSON REPORT SAVED TO:", json_path)
    print("PDF REPORT SAVED TO:", pdf_path)


if __name__ == "__main__":
    main()