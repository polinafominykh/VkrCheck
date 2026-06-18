from typing import List, Optional
from agents.formal_agent import FormalAgent
from agents.semantic_agent import SemanticAgent
from agents.structure_agent import StructureAgent
from core.schemas import CheckResult, PipelineReport
from ingestion.loader import load_document
from llm.client import LLMClient
from preprocessing.clean_text import clean_text
from segmentation.chapter_extractor import extract_chapters, normalize_sections, ensure_lines

class VKROrchestrator:
    def __init__(
        self,
        formal_criteria_path: str = "criteria/formal_criteria.yaml",
        structure_criteria_path: str = "criteria/structure_criteria.yaml",
        semantic_criteria_path: str = "criteria/semantic_criteria.yaml",
        degree: str = "master",
    ) -> None:
        self.formal_agent = FormalAgent(criteria_path=formal_criteria_path)
        self.structure_agent = StructureAgent(
            criteria_path=structure_criteria_path,
            degree=degree,
        )
        self.llm_client = LLMClient()
        self.semantic_agent = SemanticAgent(
            criteria_path=semantic_criteria_path,
            llm_client=self.llm_client,
        )
        self.degree = degree

    def run(
        self,
        file_path: str,
        enabled_agents: Optional[List[str]] = None,
    ) -> PipelineReport:
        if enabled_agents is None:
            enabled_agents = ["formal", "structure", "semantic"]

        raw = load_document(file_path)
        lines = ensure_lines(raw)
        lines = clean_text(lines)

        chapters = extract_chapters(lines)
        normalized_sections = normalize_sections(chapters)

        formal_results: List[CheckResult] = []
        semantic_results: List[CheckResult] = []

        if "formal" in enabled_agents:
            formal_report = self.formal_agent.run(
                chapters=chapters,
                normalized_sections=normalized_sections,
            )
            formal_results.extend(formal_report.results)

        if "structure" in enabled_agents:
            structure_report = self.structure_agent.run(
                normalized_sections=normalized_sections,
            )
            formal_results.extend(structure_report.results)

        if "semantic" in enabled_agents:
            semantic_report = self.semantic_agent.run(
                normalized_sections=normalized_sections,
            )
            semantic_results.extend(semantic_report.results)

        return PipelineReport(
            chapters=chapters,
            normalized_sections=normalized_sections,
            formal_results=formal_results,
            semantic_results=semantic_results,
        )