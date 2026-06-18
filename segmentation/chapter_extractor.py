import re
from typing import Dict, List, Union

SPECIAL_HEADINGS = {
    "введение": "introduction",
    "заключение": "conclusion",
    "содержание": "toc",
    "оглавление": "toc",
    "список литературы": "references",
    "список использованных источников": "references",
    "список используемых источников": "references",
    "список сокращений и условных обозначений": "abbreviations",
    "приложение": "appendix",
}

DOTS_WITH_PAGE_RE = re.compile(r"\.{3,}\s*\d+\s*$")
ONLY_PAGE_RE = re.compile(r"^\d{1,3}$")
NUMBERED_HEADING_RE = re.compile(r"^\d+(\.\d+){0,2}\s+[A-Za-zА-Яа-яЁё]")
CHAPTER_WORD_RE = re.compile(r"^(глава|chapter)\s+\d+\b", re.IGNORECASE)
BIB_ENTRY_RE = re.compile(r"^\d+\.\s+[A-ZА-ЯЁ][^\\n]{10,}$")

def ensure_lines(data: Union[str, List[str]]) -> List[str]:
    if isinstance(data, str):
        return [line.strip() for line in data.splitlines() if line.strip()]
    return [str(line).strip() for line in data if str(line).strip()]

def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def is_probably_toc_line(line: str) -> bool:
    return bool(DOTS_WITH_PAGE_RE.search(line))

def is_bad_heading_candidate(line: str) -> bool:
    if not line:
        return True

    if ONLY_PAGE_RE.fullmatch(line):
        return True

    if len(line) < 3:
        return True

    if len(line) > 120:
        return True

    forbidden_parts = [
        "обучающийся",
        "student",
        "группа/group",
        "квалификация",
        "degree level",
        "руководитель",
        "thesis supervisor",
        "consultant",
        "faculty/institute/cluster",
        "head of educational program",
        "description of the graduation thesis",
        "graduation thesis",
        "магистр",
        "документ",
    ]

    low = normalize_heading(line)
    if any(part in low for part in forbidden_parts):
        return True

    if BIB_ENTRY_RE.match(line):
        return True

    if line.count(",") >= 2:
        return True

    return False

def is_heading(line: str, after_references: bool = False) -> bool:
    line = line.strip()
    low = normalize_heading(line)

    if is_bad_heading_candidate(line):
        return False

    if is_probably_toc_line(line):
        return False

    if after_references:
        return low.startswith("приложение") or low.startswith("appendix")

    for marker in SPECIAL_HEADINGS:
        if low == marker or low.startswith(marker + " "):
            return True

    if CHAPTER_WORD_RE.match(line):
        return True

    if NUMBERED_HEADING_RE.match(line):
        if BIB_ENTRY_RE.match(line):
            return False
        return True

    words = line.split()

    if line.isupper() and 1 <= len(words) <= 10:
        return True

    if 1 <= len(words) <= 10 and not line.endswith("."):
        cap_ratio = sum(1 for w in words if w[:1].isupper()) / max(len(words), 1)
        if cap_ratio >= 0.8:
            return True

    return False

def extract_chapters(data: Union[str, List[str]]) -> Dict[str, str]:
    lines = ensure_lines(data)

    chapters: Dict[str, List[str]] = {}
    current_title = "PREFACE"
    chapters[current_title] = []

    started_main_text = False
    in_references = False

    for line in lines:
        low = normalize_heading(line)

        if not started_main_text:
            if (
                low == "введение"
                or low.startswith("1 ")
                or low.startswith("1.")
                or low == "содержание"
                or low == "оглавление"
            ):
                started_main_text = True

        if is_heading(line, after_references=in_references):
            current_title = line
            if current_title not in chapters:
                chapters[current_title] = []

            if "список литературы" in low or "список использованных источников" in low or "список используемых источников" in low:
                in_references = True

            continue

        chapters[current_title].append(line)

    result: Dict[str, str] = {}

    for title, text_lines in chapters.items():
        text = "\n".join(text_lines).strip()
        if not text:
            continue

        if title != "PREFACE" and is_bad_heading_candidate(title):
            continue

        result[title] = text

    return result

def normalize_sections(chapters: Dict[str, str]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}

    for title, text in chapters.items():
        norm = normalize_heading(title)

        if "введение" in norm:
            key = "introduction"
        elif "заключение" in norm:
            key = "conclusion"
        elif "содерж" in norm or "оглавл" in norm:
            key = "toc"
        elif "литератур" in norm or "источник" in norm:
            key = "references"
        elif "сокращени" in norm or "обозначени" in norm:
            key = "abbreviations"
        elif "прилож" in norm:
            key = "appendix"
        else:
            key = title

        normalized[key] = text

    return normalized