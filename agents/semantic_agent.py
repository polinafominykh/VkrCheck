import re
from typing import Dict, List, Tuple
from core.criteria_loader import load_yaml
from core.schemas import CheckResult, FormalReport
from llm.client import LLMClient

class SemanticAgent:
    def __init__(
        self,
        criteria_path: str = "criteria/semantic_criteria.yaml",
        llm_client: LLMClient = None,
    ) -> None:
        self.criteria = load_yaml(criteria_path)
        self.llm_client = llm_client or LLMClient()

    def run(self, normalized_sections: Dict[str, str]) -> FormalReport:
        results: List[CheckResult] = []

        results.append(self._check_introduction_semantics(normalized_sections))

        for title, text in self._extract_main_numbered_chapters(normalized_sections):
            results.append(self._check_chapter_semantics(title, text))

        return FormalReport(results=results)

    def _extract_main_numbered_chapters(
        self,
        sections: Dict[str, str],
    ) -> List[Tuple[str, str]]:

        result: List[Tuple[str, str]] = []

        for title, text in sections.items():
            if re.match(r"^\d+\s+[A-ZА-ЯЁA-Za-zА-Яа-яЁё]", title):
                result.append((title, text))

        return result

    def _check_introduction_semantics(
        self,
        normalized_sections: Dict[str, str],
    ) -> CheckResult:
        config = self.criteria.get("introduction_semantic", {})
        intro_text = normalized_sections.get("introduction", "")

        if not intro_text:
            return CheckResult(
                criterion_id="semantic_introduction",
                criterion_name="Смысловая оценка введения",
                status="fail",
                message="Введение отсутствует, смысловая проверка невозможна",
                recommendations=["Добавь раздел 'Введение'"],
            )

        if not self.llm_client.enabled:
            return CheckResult(
                criterion_id="semantic_introduction",
                criterion_name="Смысловая оценка введения",
                status="warn",
                message="LLM-клиент не настроен, смысловая проверка пропущена",
                recommendations=["Настрой подключение к модели"],
            )

        system_prompt = config.get("system_prompt", "")
        user_template = config.get("user_prompt_template", "")
        temperature = float(config.get("temperature", 0.1))

        user_prompt = user_template.format(
            introduction_text=intro_text[:12000]
        )

        data = self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

        if data.get("status") == "error":
            return CheckResult(
                criterion_id="semantic_introduction",
                criterion_name="Смысловая оценка введения",
                status="warn",
                message="LLM вернула некорректный ответ",
                evidence=[str(data.get("raw_text", data))[:1000]],
                recommendations=["Проверь промпт и формат ответа модели"],
            )

        status = data.get("status", "warn")
        summary = data.get("summary", "Смысловая проверка выполнена")
        score = data.get("score", "n/a")

        evidence: List[str] = []
        for item in data.get("found_blocks", []):
            evidence.append(f"found: {item}")
        for item in data.get("issues", [])[:5]:
            evidence.append(f"issue: {item}")

        recommendations = data.get("recommendations", [])

        if isinstance(score, (int, float)):
            message = f"{summary} Итоговая оценка: {score}/100."
        else:
            message = summary

        return CheckResult(
            criterion_id="semantic_introduction",
            criterion_name="Смысловая оценка введения",
            status=status,
            message=message,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _check_chapter_semantics(
        self,
        chapter_title: str,
        chapter_text: str,
    ) -> CheckResult:
        config = self.criteria.get("chapter_semantic", {})

        if not chapter_text.strip():
            return CheckResult(
                criterion_id=f"semantic_chapter_{chapter_title}",
                criterion_name=f"Смысловая оценка главы: {chapter_title}",
                status="warn",
                message="Текст главы пустой или не извлечен",
                recommendations=["Проверь извлечение текста главы"],
            )

        if not self.llm_client.enabled:
            return CheckResult(
                criterion_id=f"semantic_chapter_{chapter_title}",
                criterion_name=f"Смысловая оценка главы: {chapter_title}",
                status="warn",
                message="LLM-клиент не настроен, смысловая проверка главы пропущена",
            )

        system_prompt = config.get("system_prompt", "")
        user_template = config.get("user_prompt_template", "")
        temperature = float(config.get("temperature", 0.1))

        user_prompt = user_template.format(
            chapter_title=chapter_title,
            chapter_text=chapter_text[:12000],
        )

        data = self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

        if data.get("status") == "error":
            return CheckResult(
                criterion_id=f"semantic_chapter_{chapter_title}",
                criterion_name=f"Смысловая оценка главы: {chapter_title}",
                status="warn",
                message="LLM вернула некорректный ответ",
                evidence=[str(data.get("raw_text", data))[:1000]],
                recommendations=["Проверь промпт главы и формат ответа модели"],
            )

        status = data.get("status", "warn")
        summary = data.get("summary", "Смысловая проверка главы выполнена")
        score = data.get("score", "n/a")

        evidence: List[str] = []
        for item in data.get("strengths", [])[:3]:
            evidence.append(f"strength: {item}")
        for item in data.get("issues", [])[:3]:
            evidence.append(f"issue: {item}")

        recommendations = data.get("recommendations", [])

        if isinstance(score, (int, float)):
            message = f"{summary} Итоговая оценка: {score}/100."
        else:
            message = summary

        return CheckResult(
            criterion_id=f"semantic_chapter_{chapter_title}",
            criterion_name=f"Смысловая оценка главы: {chapter_title}",
            status=status,
            message=message,
            evidence=evidence,
            recommendations=recommendations,
        )