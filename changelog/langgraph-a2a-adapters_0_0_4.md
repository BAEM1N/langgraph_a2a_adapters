# 0.0.4

- X- prefix 헤더 자동 추출 지원 (환경변수 스타일)
  - `X-` prefix가 붙은 모든 HTTP 헤더를 `api_config`로 자동 전달
  - 대문자 + 언더스코어로 변환 (환경변수 컨벤션)
  - 예: `X-OPENAI-API-KEY` → `OPENAI_API_KEY`
  - 예: `X-LANGFUSE-SECRET-KEY` → `LANGFUSE_SECRET_KEY`
- Langfuse 자동 통합: `X-LANGFUSE-SECRET-KEY`, `X-LANGFUSE-PUBLIC-KEY` 헤더 전달 시 자동 활성화
- 확장성 개선: 새로운 서비스 연동 시 어댑터 코드 수정 없이 헤더만 추가하면 됨
