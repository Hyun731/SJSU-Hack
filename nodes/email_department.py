from tools.mock_tools import mock_classify_importance, mock_read_email
from services.gmail_service import read_latest_email
from services.llm_service import generate_json


def _fallback_actions(text: str, importance: str) -> list[str]:
    if importance != "high":
        return ["필요 시 나중에 확인"]

    if any(keyword in text for keyword in ["견적", "비용", "승인", "회신"]):
        return [
            "견적서와 비용 검토",
            "승인 여부 결정",
            "마감 전 회신 작성",
        ]

    if any(keyword in text for keyword in ["회의", "일정", "시간"]):
        return [
            "일정 확인",
            "참석 가능 여부 결정",
            "답장 초안 작성",
        ]

    return ["핵심 요청 확인", "필요한 후속 조치 결정", "답장 초안 작성"]


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
            "You analyze an email for a no-code AI orchestration workflow. "
            "Return only valid JSON with keys importance, reason, actions. "
            "importance must be high or normal. reason must be Korean."
            "actions must be 1 to 4 short Korean action items that match the actual email content. "
            "Do not invent unrelated actions."
        ),
        user_prompt=(
            f"Subject: {email.get('subject', '')}\n"
            f"Sender: {email.get('sender', '')}\n"
            f"Body:\n{email['body']}"
        ),
        fallback={
            "importance": fallback_importance,
            "reason": "",
            "actions": _fallback_actions(email["body"], fallback_importance),
        },
        max_output_tokens=350,
    )
    importance = result.get("importance")
    if importance not in {"high", "normal"}:
        importance = fallback_importance
    actions = result.get("actions")
    if not isinstance(actions, list) or not all(isinstance(action, str) for action in actions):
        actions = _fallback_actions(email["body"], importance)
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
        "actions": [*state.get("actions", []), *actions],
    }
