def mock_read_email(text: str) -> dict:
    return {
        "subject": "Mock important email",
        "sender": "colleague@example.com",
        "body": text or "내일 오후 3시에 회의 가능하신가요? 발표 자료도 함께 확인 부탁드립니다.",
    }


def mock_classify_importance(text: str) -> str:
    important_keywords = ["회의", "발표", "urgent", "중요", "마감", "계약", "확인"]
    normalized = text.lower()
    return "high" if any(keyword in normalized for keyword in important_keywords) else "normal"


def mock_summarize(text: str) -> str:
    normalized = " ".join((text or "").split())
    if not normalized:
        return "처리할 내용이 비어 있습니다."
    if "회의" in normalized and "발표" in normalized:
        return "내일 오후 3시 회의 가능 여부와 발표 자료 확인 요청이 포함되어 있습니다."
    if len(normalized) <= 90:
        return normalized
    return normalized[:87] + "..."


def mock_parse_document(text: str) -> dict:
    content = text or "문서 내용이 제공되지 않았습니다."
    return {
        "title": "Mock Document",
        "content": content,
        "sections": [section.strip() for section in content.split("\n") if section.strip()],
    }


def mock_research_news(topic: str) -> list[str]:
    topic = topic or "AI orchestration"
    return [
        f"{topic} 관련 주요 동향을 확인했습니다.",
        f"{topic} 시장에서 자동화와 요약 기능 수요가 증가하고 있습니다.",
        f"{topic} 워크플로우는 mock research 결과로 생성되었습니다.",
    ]


def mock_create_report(summary: str, actions: list[str]) -> dict:
    return {
        "title": "왕에게 보고드립니다",
        "summary": summary,
        "actions": actions,
    }
