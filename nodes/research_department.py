from tools.mock_tools import mock_research_news


def research_department_node(state: dict) -> dict:
    topic = state.get("input", {}).get("topic") or state.get("input", {}).get("text") or "AI"
    findings = mock_research_news(topic)

    return {
        **state,
        "research_findings": findings,
        "source_text": " ".join(findings),
        "steps": [
            *state.get("steps", []),
            {
                "nodeId": "research_department",
                "status": "success",
                "message": "뉴스와 리서치 결과를 수집했습니다.",
            },
        ],
        "actions": [*state.get("actions", []), "주요 뉴스 확인", "관심 주제 저장"],
    }
