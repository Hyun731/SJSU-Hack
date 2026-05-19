from tools.mock_tools import mock_classify_importance, mock_read_email
from services.gmail_service import read_latest_email
from services.llm_service import generate_json, is_openai_enabled


def email_department_node(state: dict) -> dict:
    input_data = state.get("input", {})
    email_text = input_data.get("sampleEmailText") or input_data.get("text", "")
    should_read_gmail = input_data.get("useLatestGmail", False) or not email_text

    if should_read_gmail:
        try:
            email = read_latest_email()
        except Exception as exc:
            return {
                **state,
                "source_text": "",
                "email": {},
                "importance": "normal",
                "summary": "Gmail 연결 또는 최신 이메일 조회에 실패했습니다.",
                "steps": [
                    *state.get("steps", []),
                    {
                        "nodeId": "email_department",
                        "status": "error",
                        "message": f"Gmail 이메일을 읽지 못했습니다: {exc}",
                    },
                ],
                "actions": [
                    *state.get("actions", []),
                    "Google OAuth 연결 상태 확인",
                    "Gmail 권한 scope 확인",
                ],
            }
    else:
        email = mock_read_email(email_text)

    fallback_importance = mock_classify_importance(email["body"])
    result = generate_json(
        system_prompt=(
            "You classify email importance for an orchestration workflow. "
            "Return only valid JSON with keys importance and reason. "
            "importance must be high or normal. reason must be Korean."
        ),
        user_prompt=email["body"],
        fallback={"importance": fallback_importance, "reason": ""},
        max_output_tokens=200,
    )
    importance = result.get("importance") if is_openai_enabled() else fallback_importance
    if importance not in {"high", "normal"}:
        importance = fallback_importance
    message = (
        "이메일 중요도를 높음으로 분류했습니다."
        if importance == "high"
        else "이메일 중요도를 보통으로 분류했습니다."
    )

    return {
        **state,
        "source_text": email["body"],
        "email": email,
        "importance": importance,
        "steps": [
            *state.get("steps", []),
            {"nodeId": "email_department", "status": "success", "message": message},
        ],
        "actions": [
            *state.get("actions", []),
            "캘린더 확인 필요",
            "발표 자료 검토 필요",
            "답장 초안 작성 가능",
        ]
        if importance == "high"
        else [*state.get("actions", []), "필요 시 나중에 확인"],
    }
