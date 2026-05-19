from tools.mock_tools import mock_summarize
from services.llm_service import summarize_text


def summary_department_node(state: dict) -> dict:
    source_text = state.get("source_text") or state.get("input", {}).get("text", "")
    fallback_summary = mock_summarize(source_text)
    summary = summarize_text(
        source_text,
        context="oh-my-kingdom Department가 처리한 내용을 왕에게 보고하기 위한 요약",
        fallback_summary=fallback_summary,
    )

    if state.get("importance") == "high":
        summary = f"중요 이메일 1건을 발견했습니다. {summary}"

    return {
        **state,
        "summary": summary,
        "steps": [
            *state.get("steps", []),
            {
                "nodeId": "summary_department",
                "status": "success",
                "message": "핵심 내용을 요약했습니다.",
            },
        ],
    }
