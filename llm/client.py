import json
import re
from typing import Any, Dict, Optional
from openai import OpenAI

class LLMClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        self.base_url = base_url or "http://10.32.2.11:8041/v1"
        self.api_key = api_key or "token-abc123"
        self.model_name = model_name or "qwen3-32b"

        self.enabled = bool(self.base_url and self.api_key and self.model_name)

        self.client = None
        if self.enabled:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        if not self.enabled or self.client is None:
            return {
                "status": "error",
                "message": "LLM client is not configured",
            }

        response = self.client.chat.completions.create(
            model=self.model_name,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content or ""
        return self._safe_parse_json(content)

    def _safe_parse_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()

        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1).strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace_match:
            try:
                data = json.loads(brace_match.group(1))
                if isinstance(data, dict):
                    return data
            except Exception:
                pass

        return {
            "status": "error",
            "message": "Failed to parse model response as JSON",
            "raw_text": text,
        }