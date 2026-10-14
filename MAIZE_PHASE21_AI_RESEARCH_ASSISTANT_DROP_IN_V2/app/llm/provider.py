from __future__ import annotations
import json, time
import httpx
from ..config import LLM_PROVIDER, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

class LLMError(RuntimeError): pass

class BaseProvider:
    def available(self)->bool: return False
    def chat(self, messages:list[dict], temperature:float=0.1)->str: raise LLMError("Provider unavailable")

class OpenAICompatibleProvider(BaseProvider):
    def available(self)->bool: return bool(LLM_BASE_URL and LLM_MODEL and LLM_API_KEY)
    def chat(self, messages, temperature=0.1):
        if not self.available(): raise LLMError("OpenAI-compatible provider not configured")
        headers={"Authorization":f"Bearer {LLM_API_KEY}","Content-Type":"application/json"}
        payload={"model":LLM_MODEL,"messages":messages,"temperature":temperature}
        url=LLM_BASE_URL+"/chat/completions" if not LLM_BASE_URL.endswith("/chat/completions") else LLM_BASE_URL
        r=httpx.post(url,headers=headers,json=payload,timeout=60)
        r.raise_for_status(); data=r.json()
        try: return data["choices"][0]["message"]["content"] or ""
        except Exception as exc: raise LLMError(f"Unexpected LLM response: {exc}")

class ProviderFactory:
    @staticmethod
    def get():
        if LLM_PROVIDER in {"openai","openai_compatible","ollama","local"} and LLM_PROVIDER!="local":
            p=OpenAICompatibleProvider()
            return p if p.available() else None
        return None
