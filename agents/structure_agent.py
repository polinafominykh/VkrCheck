import re
from typing import Dict, List
from core.criteria_loader import load_yaml
from core.schemas import CheckResult, FormalReport

class StructureAgent:
    def __init__(self, criteria_path: str = "criteria/structure_criteria.yaml", degree: str = "master") -> None:
        self.criteria = load_yaml(criteria_path)
        self.degree = degree.lower().strip()

    def run(self, normalized_sections: Dict[str, str]) -> FormalReport:
        results: List[CheckResult] = []
        results.append(self._check_introduction_blocks(normalized_sections))
        return FormalReport(results=results)

    def _normalize_text(self, text: str) -> str:
        text = text.lower()
        text = text.replace("ё", "е")
        text = re.sub(r"-\s*\n\s*", "", text)
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _check_introduction_blocks(self, normalized_sections: Dict[str, str]) -> CheckResult:
        intro_text = normalized_sections.get("introduction", "")
        if not intro_text:
            return CheckResult(
                criterion_id="intro_blocks",
                criterion_name="Структура введения",
                status="fail",
                message="Введение отсутствует, проверить структуру введения невозможно",
                recommendations=["Добавь раздел 'Введение'"],
            )

        intro_norm = self._normalize_text(intro_text)

        common = self.criteria.get("introduction_blocks", {}).get("required_common", {})
        found_common = self._find_blocks(intro_norm, common)

        missing_common = [key for key in common.keys() if key not in found_common]
        min_common = self.criteria.get("thresholds", {}).get("min_found_common_blocks", 4)

        evidence = [f"{k}: найдено" for k in found_common]

        if len(found_common) < min_common:
            return CheckResult(
                criterion_id="intro_blocks_common",
                criterion_name="Структура введения",
                status="fail",
                message=(
                    f"Во введении найдено слишком мало обязательных смысловых блоков: "
                    f"{len(found_common)} из {len(common)}"
                ),
                evidence=evidence,
                recommendations=[
                    f"Добавь или явно обозначь блоки: {', '.join(missing_common)}"
                ],
            )

        if self.degree == "master":
            master_blocks = self.criteria.get("introduction_blocks", {}).get("required_master", {})
            found_master = self._find_blocks(intro_norm, master_blocks)
            missing_master = [key for key in master_blocks.keys() if key not in found_master]
            min_master = self.criteria.get("thresholds", {}).get("min_found_master_blocks", 1)

            evidence.extend([f"{k}: найдено" for k in found_master])

            if len(found_master) < min_master:
                return CheckResult(
                    criterion_id="intro_blocks_master",
                    criterion_name="Структура введения магистерской ВКР",
                    status="warn",
                    message=(
                        f"Во введении магистерской ВКР найдено мало специальных блоков: "
                        f"{len(found_master)} из {len(master_blocks)}"
                    ),
                    evidence=evidence,
                    recommendations=[
                        f"Желательно явно отразить: {', '.join(missing_master)}"
                    ],
                )

        return CheckResult(
            criterion_id="intro_blocks",
            criterion_name="Структура введения",
            status="pass",
            message="Структура введения выглядит корректно",
            evidence=evidence,
        )

    def _find_blocks(self, text: str, blocks: Dict[str, List[str]]) -> List[str]:
        found = []

        for block_name, markers in blocks.items():
            for marker in markers:
                marker_norm = self._normalize_text(marker)
                if marker_norm in text:
                    found.append(block_name)
                    break

        return found