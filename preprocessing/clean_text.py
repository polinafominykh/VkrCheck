import re
from typing import List, Union

def clean_text(data: Union[str, List[str]]) -> List[str]:

    if isinstance(data, str):
        lines = data.splitlines()
    else:
        lines = data

    cleaned: List[str] = []

    for line in lines:
        if line is None:
            continue

        line = str(line)
        line = line.replace("\xa0", " ")
        line = re.sub(r"[ \t]+", " ", line)
        line = line.strip()

        if not line:
            continue

        if re.fullmatch(r"\d{1,3}", line):
            continue

        if len(line) == 1 and line.isalpha():
            continue

        cleaned.append(line)

    return cleaned