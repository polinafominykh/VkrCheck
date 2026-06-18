import re
from typing import Dict, List

from core.criteria_loader import load_yaml
from core.schemas import CheckResult, FormalReport


class FormalAgent:
    def __init__(self, criteria_path: str = "criteria/formal_criteria.yaml") -> None:
        self.criteria = load_yaml(criteria_path)

    def run(self, chapters: Dict[str, str], normalized_sections: Dict[str, str]) -> FormalReport:
        results: List[CheckResult] = []

        results.append(self._check_required_sections(normalized_sections))
        results.append(self._check_top_level_chapters(chapters))
        results.append(self._check_introduction(normalized_sections))
        results.append(self._check_references(normalized_sections))

        return FormalReport(results=results)

    def _check_required_sections(self, normalized_sections: Dict[str, str]) -> CheckResult:
        required = self.criteria.get("required_sections", [])
        missing = [section for section in required if section not in normalized_sections]

        if missing:
            return CheckResult(
                criterion_id="required_sections",
                criterion_name="Обязательные разделы",
                status="fail",
                message=f"Отсутствуют обязательные разделы: {', '.join(missing)}",
                evidence=list(normalized_sections.keys()),
                recommendations=[
                    "Проверь, что в работе есть введение, заключение и список источников",
                    "Проверь корректность заголовков разделов"
                ],
            )

        return CheckResult(
            criterion_id="required_sections",
            criterion_name="Обязательные разделы",
            status="pass",
            message="Обязательные разделы найдены",
            evidence=list(normalized_sections.keys()),
        )

    def _check_top_level_chapters(self, chapters: Dict[str, str]) -> CheckResult:
        pattern = self.criteria.get("patterns", {}).get("top_level_chapter", r"^\d+\s+")
        min_count = self.criteria.get("thresholds", {}).get("min_top_level_chapters", 2)
        max_count = self.criteria.get("thresholds", {}).get("max_top_level_chapters", 8)

        numbered = [title for title in chapters.keys() if re.match(pattern, title)]
        count = len(numbered)

        if count < min_count:
            return CheckResult(
                criterion_id="top_level_chapters",
                criterion_name="Нумерованные главы",
                status="fail",
                message=f"Найдено слишком мало глав верхнего уровня: {count}",
                evidence=numbered,
                recommendations=[
                    "Проверь, что основные главы оформлены как 1 ..., 2 ..., 3 ..."
                ],
            )

        if count > max_count:
            return CheckResult(
                criterion_id="top_level_chapters",
                criterion_name="Нумерованные главы",
                status="warn",
                message=f"Найдено необычно много глав верхнего уровня: {count}",
                evidence=numbered,
                recommendations=[
                    "Проверь, не приняла ли сегментация часть служебных строк за главы"
                ],
            )

        return CheckResult(
            criterion_id="top_level_chapters",
            criterion_name="Нумерованные главы",
            status="pass",
            message=f"Количество глав верхнего уровня в норме: {count}",
            evidence=numbered,
        )

    def _check_introduction(self, normalized_sections: Dict[str, str]) -> CheckResult:
        intro_text = normalized_sections.get("introduction", "")
        min_chars = self.criteria.get("thresholds", {}).get("min_introduction_chars", 500)

        if not intro_text:
            return CheckResult(
                criterion_id="introduction_presence",
                criterion_name="Введение",
                status="fail",
                message="Раздел 'Введение' не найден",
                recommendations=["Добавь введение или проверь заголовок раздела"],
            )

        if len(intro_text) < min_chars:
            return CheckResult(
                criterion_id="introduction_size",
                criterion_name="Объем введения",
                status="warn",
                message=f"Введение найдено, но выглядит слишком коротким: {len(intro_text)} символов",
                evidence=[intro_text[:300]],
                recommendations=[
                    "Проверь, полностью ли извлекся текст введения",
                    "Проверь, раскрыты ли актуальность, цель, задачи и практическая значимость"
                ],
            )

        return CheckResult(
            criterion_id="introduction_size",
            criterion_name="Объем введения",
            status="pass",
            message=f"Введение найдено, объем выглядит достаточным: {len(intro_text)} символов",
            evidence=[intro_text[:300]],
        )

    def _check_references(self, normalized_sections: Dict[str, str]) -> CheckResult:
        references_text = normalized_sections.get("references", "")
        ref_pattern = self.criteria.get("patterns", {}).get("reference_item", r"^\d+[\.\)]?\s+")
        min_items = self.criteria.get("thresholds", {}).get("min_reference_items", 5)

        if not references_text:
            return CheckResult(
                criterion_id="references_presence",
                criterion_name="Список источников",
                status="fail",
                message="Список источников не найден",
                recommendations=["Добавь список использованных источников"],
            )

        items = []
        for line in references_text.splitlines():
            if re.match(ref_pattern, line.strip()):
                items.append(line.strip())

        if len(items) < min_items:
            return CheckResult(
                criterion_id="references_count",
                criterion_name="Количество источников",
                status="warn",
                message=f"Найдено мало источников: {len(items)}",
                evidence=items[:10],
                recommendations=[
                    "Проверь, корректно ли извлекся список литературы",
                    "Проверь оформление нумерации источников"
                ],
            )

        return CheckResult(
            criterion_id="references_count",
            criterion_name="Количество источников",
            status="pass",
            message=f"Список источников найден, позиций: {len(items)}",
            evidence=items[:10],
        )