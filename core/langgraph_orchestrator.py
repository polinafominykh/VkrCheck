from typing import Any, Dict, List, TypedDict
from langgraph.graph import StateGraph, START, END
from agents.formal_agent import FormalAgent
from agents.semantic_agent import SemanticAgent
from agents.structure_agent import StructureAgent
from core.schemas import CheckResult, PipelineReport
from ingestion.loader import load_pdf
from llm.client import LLMClient
from preprocessing.clean_text import clean_text
from segmentation.chapter_extractor import extract_chapters, normalize_sections, ensure_lines

class VKRGraphState(TypedDict, total=False):
    file_path: str
    raw: Any
    lines: List[str]
    chapters: Dict[str, str]
    normalized_sections: Dict[str, str]
    formal_results: List[CheckResult]
    semantic_results: List[CheckResult]
    degree: str

class VKRLangGraphOrchestrator:
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
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(VKRGraphState)

        builder.add_node("load_document", self._load_document_node)
        builder.add_node("clean_document", self._clean_document_node)
        builder.add_node("segment_document", self._segment_document_node)
        builder.add_node("formal_checks", self._formal_checks_node)
        builder.add_node("semantic_checks", self._semantic_checks_node)

        builder.add_edge(START, "load_document")
        builder.add_edge("load_document", "clean_document")
        builder.add_edge("clean_document", "segment_document")
        builder.add_edge("segment_document", "formal_checks")
        builder.add_edge("formal_checks", "semantic_checks")
        builder.add_edge("semantic_checks", END)

        return builder.compile()

    def _load_document_node(self, state: VKRGraphState) -> VKRGraphState:
        file_path = state["file_path"]
        raw = load_pdf(file_path)
        return {"raw": raw}

    def _clean_document_node(self, state: VKRGraphState) -> VKRGraphState:
        raw = state["raw"]
        lines = ensure_lines(raw)
        lines = clean_text(lines)
        return {"lines": lines}

    def _segment_document_node(self, state: VKRGraphState) -> VKRGraphState:
        lines = state["lines"]
        chapters = extract_chapters(lines)
        normalized_sections = normalize_sections(chapters)
        return {
            "chapters": chapters,
            "normalized_sections": normalized_sections,
        }

    def _formal_checks_node(self, state: VKRGraphState) -> VKRGraphState:
        chapters = state["chapters"]
        normalized_sections = state["normalized_sections"]

        formal_report = self.formal_agent.run(
            chapters=chapters,
            normalized_sections=normalized_sections,
        )

        structure_report = self.structure_agent.run(
            normalized_sections=normalized_sections,
        )

        formal_results = formal_report.results + structure_report.results
        return {"formal_results": formal_results}

    def _semantic_checks_node(self, state: VKRGraphState) -> VKRGraphState:
        normalized_sections = state["normalized_sections"]

        semantic_report = self.semantic_agent.run(
            normalized_sections=normalized_sections,
        )

        return {"semantic_results": semantic_report.results}

    def run(self, file_path: str) -> PipelineReport:
        final_state = self.graph.invoke(
            {
                "file_path": file_path,
                "degree": self.degree,
            }
        )

        return PipelineReport(
            chapters=final_state.get("chapters", {}),
            normalized_sections=final_state.get("normalized_sections", {}),
            formal_results=final_state.get("formal_results", []),
            semantic_results=final_state.get("semantic_results", []),
        )