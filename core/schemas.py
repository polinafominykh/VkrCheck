from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class CheckResult:
    criterion_id: str
    criterion_name: str
    status: str  # pass / warn / fail
    message: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class FormalReport:
    results: List[CheckResult]

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "pass")

    @property
    def warned(self) -> int:
        return sum(1 for r in self.results if r.status == "warn")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "fail")

@dataclass
class PipelineReport:
    chapters: Dict[str, str]
    normalized_sections: Dict[str, str]
    formal_results: List[CheckResult]
    semantic_results: List[CheckResult] = field(default_factory=list)

    @property
    def all_results(self) -> List[CheckResult]:
        return self.formal_results + self.semantic_results

    @property
    def passed(self) -> int:
        return sum(1 for r in self.all_results if r.status == "pass")

    @property
    def warned(self) -> int:
        return sum(1 for r in self.all_results if r.status == "warn")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.all_results if r.status == "fail")