"""
LLM 클라이언트 래퍼
OpenAI 형식 또는 MLX 직접 호출 방식 지원
"""

import json
import re
import threading
from typing import Optional, Dict, Any, List
from ..config import Config


# MLX 모델 싱글톤 (재로딩 방지)
_mlx_model = None
_mlx_tokenizer = None
# Metal GPU 동시 접근 방지 락
_mlx_lock = threading.Lock()


def _get_mlx_model(model_name: str):
    global _mlx_model, _mlx_tokenizer
    if _mlx_model is None:
        import mlx_lm
        print(f"[MLX] 모델 로딩 중: {model_name}")
        _mlx_model, _mlx_tokenizer = mlx_lm.load(model_name)
        print(f"[MLX] 모델 로딩 완료")
    return _mlx_model, _mlx_tokenizer


def _messages_to_prompt(tokenizer, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
    """메시지 목록을 모델의 채팅 템플릿으로 변환"""
    if json_mode:
        # JSON 모드: 시스템 메시지에 JSON 요청 추가
        modified = []
        injected = False
        for msg in messages:
            if msg["role"] == "system" and not injected:
                modified.append({
                    "role": "system",
                    "content": msg["content"] + "\n\n반드시 유효한 JSON 형식으로만 응답하세요. 코드 블록 없이 순수 JSON만 출력하세요."
                })
                injected = True
            else:
                modified.append(msg)
        if not injected:
            modified.insert(0, {
                "role": "system",
                "content": "반드시 유효한 JSON 형식으로만 응답하세요. 코드 블록 없이 순수 JSON만 출력하세요."
            })
        messages = modified

    if hasattr(tokenizer, 'apply_chat_template'):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )
        except TypeError:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

    # 폴백: 수동으로 프롬프트 구성
    prompt = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            prompt += f"System: {content}\n\n"
        elif role == "user":
            prompt += f"User: {content}\n\nAssistant: "
        elif role == "assistant":
            prompt += f"{content}\n\nUser: "
    return prompt


class LLMClient:
    """LLM 클라이언트 - OpenAI API 또는 MLX 직접 호출"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY가 설정되지 않았습니다")

        # api_key가 'mlx'이면 MLX 직접 모드
        self.use_mlx = (self.api_key.lower() == 'mlx')

        if not self.use_mlx:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        if self.use_mlx:
            return self._mlx_chat(messages, temperature, max_tokens)
        return self._openai_chat(messages, temperature, max_tokens, response_format)

    def _openai_chat(self, messages, temperature, max_tokens, response_format) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def _mlx_chat(self, messages, temperature, max_tokens) -> str:
        import mlx_lm
        from mlx_lm.sample_utils import make_sampler
        with _mlx_lock:
            model, tokenizer = _get_mlx_model(self.model)
            prompt = _messages_to_prompt(tokenizer, messages)
            sampler = make_sampler(temp=temperature)
            response = mlx_lm.generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
                sampler=sampler,
                verbose=False
            )
        content = re.sub(r'<think>[\s\S]*?</think>', '', response).strip()
        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        if self.use_mlx:
            return self._mlx_chat_json(messages, temperature, max_tokens)

        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        return self._parse_json(response)

    def _mlx_chat_json(self, messages, temperature, max_tokens) -> Dict[str, Any]:
        import mlx_lm
        from mlx_lm.sample_utils import make_sampler
        with _mlx_lock:
            model, tokenizer = _get_mlx_model(self.model)
            prompt = _messages_to_prompt(tokenizer, messages, json_mode=True)
            sampler = make_sampler(temp=temperature)
            response = mlx_lm.generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
                sampler=sampler,
                verbose=False
            )
        response = re.sub(r'<think>[\s\S]*?</think>', '', response).strip()
        return self._parse_json(response)

    def _parse_json(self, response: str) -> Dict[str, Any]:
        cleaned = response.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        cleaned = cleaned.strip()

        # JSON 블록 추출 시도
        if not cleaned.startswith('{') and not cleaned.startswith('['):
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                cleaned = match.group(0)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"LLM이 유효하지 않은 JSON을 반환했습니다: {cleaned[:200]}")
