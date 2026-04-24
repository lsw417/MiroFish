"""
LLM 테스트 스크립트
현재 .env 설정으로 LLM 연결 확인
"""
import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# .env 로드
from dotenv import load_dotenv
load_dotenv()

from app.utils.llm_client import LLMClient

def test_basic():
    print("=== LLM 기본 테스트 ===")
    client = LLMClient()
    print(f"모드: {'MLX 직접' if client.use_mlx else 'OpenAI API'}")
    print(f"모델: {client.model}")
    print()

    messages = [
        {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다. 한국어로 답변하세요."},
        {"role": "user", "content": "안녕하세요! 간단하게 자기소개 한 문장만 해주세요."}
    ]

    print("질문: 안녕하세요! 간단하게 자기소개 한 문장만 해주세요.")
    print("응답 생성 중...")
    response = client.chat(messages, temperature=0.7, max_tokens=200)
    print(f"응답: {response}")
    print()

def test_json():
    print("=== JSON 모드 테스트 ===")
    client = LLMClient()

    messages = [
        {"role": "system", "content": "당신은 데이터 분석가입니다."},
        {"role": "user", "content": '다음 JSON 형식으로 한국 경제 트렌드 3가지를 반환하세요: {"trends": [{"name": "...", "description": "..."}]}'}
    ]

    print("JSON 응답 생성 중...")
    result = client.chat_json(messages, temperature=0.3, max_tokens=500)
    import json
    print(f"응답:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
    print()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "basic"

    if mode == "json":
        test_json()
    elif mode == "both":
        test_basic()
        test_json()
    else:
        test_basic()

    print("✅ 테스트 완료")
