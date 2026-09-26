"""
Provider-agnostic LLM Client supporting OpenAI, Anthropic, Gemini, DeepSeek, Groq, Ollama, and OpenRouter.
Uses lightweight urllib for zero external runtime dependencies and rock-solid timeout handling.
"""

import json
import re
from typing import Any, Dict, Optional
from urllib import request as urlrequest, error as urlerror
from app.config import settings


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.timeout = 15

    def is_available(self) -> bool:
        if not self.provider:
            return False
        if self.provider == "ollama":
            return True
        return bool(self.api_key)

    def complete(self, prompt: str, system: str = "") -> Optional[str]:
        if not self.is_available():
            return None

        try:
            if self.provider == "openai":
                return self._complete_openai(prompt, system)
            elif self.provider == "anthropic":
                return self._complete_anthropic(prompt, system)
            elif self.provider == "gemini":
                return self._complete_gemini(prompt, system)
            elif self.provider == "deepseek":
                return self._complete_deepseek(prompt, system)
            elif self.provider == "groq":
                return self._complete_groq(prompt, system)
            elif self.provider == "ollama":
                return self._complete_ollama(prompt, system)
            elif self.provider == "openrouter":
                return self._complete_openrouter(prompt, system)
            else:
                return None
        except Exception:
            return None

    def complete_json(self, prompt: str, system: str = "") -> Optional[Dict[str, Any]]:
        resp = self.complete(prompt, system)
        if not resp:
            return None
        try:
            match = re.search(r"\{[\s\S]*\}", resp)
            if match:
                return json.loads(match.group())
            return json.loads(resp)
        except Exception:
            return None

    def _complete_openai(self, prompt: str, system: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.model or "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 1000
        }).encode("utf-8")

        req = urlrequest.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _complete_anthropic(self, prompt: str, system: str) -> str:
        body_dict = {
            "model": self.model or "claude-3-5-sonnet-20241022",
            "max_tokens": 1000,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system:
            body_dict["system"] = system

        req = urlrequest.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(body_dict).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        )
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"]

    def _complete_gemini(self, prompt: str, system: str) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        body = json.dumps({
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 1000}
        }).encode("utf-8")

        model_name = self.model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        req = urlrequest.Request(url, data=body, headers={"Content-Type": "application/json"})
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _complete_deepseek(self, prompt: str, system: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.model or "deepseek-chat",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 1000
        }).encode("utf-8")

        req = urlrequest.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _complete_groq(self, prompt: str, system: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.model or "llama-3.1-70b-versatile",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 1000
        }).encode("utf-8")

        req = urlrequest.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _complete_ollama(self, prompt: str, system: str) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        body = json.dumps({
            "model": self.model or "llama3",
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": 0.0}
        }).encode("utf-8")

        req = urlrequest.Request(
            "http://localhost:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["response"]

    def _complete_openrouter(self, prompt: str, system: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.model or "anthropic/claude-3-haiku",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 1000
        }).encode("utf-8")

        req = urlrequest.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://magicpin.com"
            }
        )
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


llm_client = LLMClient()
