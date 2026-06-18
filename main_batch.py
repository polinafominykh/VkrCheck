from pathlib import Path
from core.batch_runner import find_batch_files
from core.orchestrator import VKROrchestrator
from reporting.archive_report import (
    prepare_batch_output,
    copy_work_to_output,
    build_report_pdf_path,
    build_report_json_path,
    make_zip_archive,
)
from reporting.json_report import save_pipeline_report_json
from reporting.pdf_report import save_pipeline_report_pdf

def main():
    input_dir = "input_batch"
    output_paths = prepare_batch_output("output_batch")

    files = find_batch_files(input_dir)
    print(f"Найдено файлов: {len(files)}")

    orchestrator = VKROrchestrator(
        formal_criteria_path="criteria/formal_criteria.yaml",
        structure_criteria_path="criteria/structure_criteria.yaml",
        semantic_criteria_path="criteria/semantic_criteria.yaml",
        degree="master",
    )

    processed = 0
    failed = []

    for file_path in files:
        try:
            print(f"\nОбработка: {file_path.name}")

            report = orchestrator.run(str(file_path))

            copy_work_to_output(file_path, output_paths["works"])

            json_path = build_report_json_path(file_path, output_paths["reports"])
            pdf_path = build_report_pdf_path(file_path, output_paths["reports"])

            save_pipeline_report_json(report, str(json_path))
            save_pipeline_report_pdf(report, str(pdf_path))

            print(f"  PASS={report.passed} WARN={report.warned} FAIL={report.failed}")
            processed += 1

        except Exception as e:
            print(f"  Ошибка: {e}")
            failed.append((file_path.name, str(e)))

    zip_path = make_zip_archive(output_paths["root"], output_paths["zip"])

    print("\n=== ИТОГ ===")
    print("Успешно обработано:", processed)
    print("Ошибок:", len(failed))
    print("Архив:", zip_path)

    if failed:
        print("\n=== ОШИБКИ ===")
        for name, err in failed:
            print(f"{name}: {err}")

if __name__ == "__main__":
    main()