from tools.mock_tools import mock_create_report
from services.llm_service import create_royal_report


def report_department_node(state: dict) -> dict:
    summary = state.get("summary") or "요청하신 작업을 mock workflow로 처리했습니다."
    actions = state.get("actions") or ["다음 명령 입력 가능"]
    fallback_report = mock_create_report(summary, actions)
    report = create_royal_report(summary, actions, fallback_report)

    return {
        **state,
        "report": report,
        "steps": [
            *state.get("steps", []),
            {
                "nodeId": "report_department",
                "status": "success",
                "message": "최종 보고서를 생성했습니다.",
            },
        ],
    }
