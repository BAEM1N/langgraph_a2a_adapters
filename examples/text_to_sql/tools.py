"""A2A 클라이언트 도구."""

import uuid
import httpx
from langchain_core.tools import tool


@tool
def search_web(query: str) -> str:
    """웹에서 정보를 검색합니다. 아티스트, 앨범, 음악 관련 추가 정보가 필요할 때 사용하세요."""
    try:
        with httpx.Client(timeout=120.0) as http:
            # JSON-RPC 요청
            response = http.post(
                "http://localhost:8002/",
                json={
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "message/send",
                    "params": {
                        "message": {
                            "role": "user",
                            "messageId": str(uuid.uuid4()),
                            "parts": [{"kind": "text", "text": query}],
                        }
                    },
                },
            )
            data = response.json()

            if "error" in data:
                return f"검색 실패: {data['error']}"

            result = data.get("result", {})
            history = result.get("history", [])

            for msg in history:
                if msg.get("role") == "agent":
                    for part in msg.get("parts", []):
                        if part.get("kind") == "text":
                            return part.get("text", "")

            return "검색 결과 없음"

    except Exception as e:
        return f"Search Agent 연결 실패: {e}"
