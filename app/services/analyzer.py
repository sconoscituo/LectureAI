import json
import re
import google.generativeai as genai
from app.config import get_settings

settings = get_settings()

# Gemini 클라이언트 초기화
genai.configure(api_key=settings.gemini_api_key)
_gemini_model = genai.GenerativeModel("gemini-1.5-flash")


def _clean_json_response(text: str) -> str:
    """Gemini 응답에서 마크다운 코드블록 제거 후 순수 JSON만 추출"""
    # ```json ... ``` 또는 ``` ... ``` 패턴 제거
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


async def analyze_lecture(transcript: str) -> dict:
    """
    Gemini AI를 사용해 강의 텍스트를 분석하여 요약/키워드/퀴즈/마인드맵 생성

    Args:
        transcript: Whisper로 변환된 강의 텍스트

    Returns:
        {
            "summary": str,           # 핵심 요약 (3-5문장)
            "keywords": [str],         # 핵심 키워드 (5-10개)
            "quiz": [                  # 퀴즈 (3-5문제)
                {
                    "question": str,
                    "options": [str, str, str, str],
                    "answer": str
                }
            ],
            "mindmap": {               # 마인드맵
                "topic": str,
                "children": [
                    {"topic": str, "children": [...]}
                ]
            }
        }
    """
    if not transcript or len(transcript.strip()) < 10:
        return _empty_result()

    prompt = f"""
다음은 강의/녹음 파일에서 추출한 텍스트입니다.

[강의 텍스트]
{transcript[:8000]}

위 내용을 분석하여 아래 형식의 JSON을 반환하세요.
다른 설명 없이 JSON만 반환하세요.

{{
  "summary": "강의 핵심 내용을 3~5문장으로 요약",
  "keywords": ["핵심키워드1", "핵심키워드2", "핵심키워드3", "핵심키워드4", "핵심키워드5"],
  "quiz": [
    {{
      "question": "강의 내용 기반 질문",
      "options": ["선택지A", "선택지B", "선택지C", "선택지D"],
      "answer": "선택지A"
    }}
  ],
  "mindmap": {{
    "topic": "강의 중심 주제",
    "children": [
      {{
        "topic": "주요 개념1",
        "children": [
          {{"topic": "세부내용1", "children": []}},
          {{"topic": "세부내용2", "children": []}}
        ]
      }},
      {{
        "topic": "주요 개념2",
        "children": []
      }}
    ]
  }}
}}

요구사항:
- keywords는 5~10개
- quiz는 3~5문제, 각 문제는 선택지 4개
- answer는 반드시 options 중 하나와 동일한 문자열
- 모든 내용은 한국어로 작성
- JSON 형식 엄수
"""

    try:
        response = _gemini_model.generate_content(prompt)
        raw_text = response.text
        clean_text = _clean_json_response(raw_text)
        result = json.loads(clean_text)

        # 필수 키 누락 시 빈 값으로 보완
        result.setdefault("summary", "요약을 생성하지 못했습니다.")
        result.setdefault("keywords", [])
        result.setdefault("quiz", [])
        result.setdefault("mindmap", {"topic": "분석 결과", "children": []})

        return result

    except json.JSONDecodeError as e:
        # JSON 파싱 실패 시 기본값 반환
        return _empty_result(error=f"JSON 파싱 오류: {str(e)}")
    except Exception as e:
        return _empty_result(error=f"Gemini API 오류: {str(e)}")


def _empty_result(error: str = "") -> dict:
    """분석 실패 시 반환할 빈 결과"""
    return {
        "summary": error or "텍스트가 너무 짧아 분석할 수 없습니다.",
        "keywords": [],
        "quiz": [],
        "mindmap": {"topic": "분석 불가", "children": []},
    }
