from docx import Document

def load_docx(path: str) -> str:
    doc = Document(path)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)

    return "\n".join(text)