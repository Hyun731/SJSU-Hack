from tools.mock_tools import mock_parse_document


def document_department_node(state: dict) -> dict:
    text = state.get("input", {}).get("documentText") or state.get("input", {}).get("text", "")
    document = mock_parse_document(text)

    return {
        **state,
        "document": document,
        "source_text": document["content"],
        "steps": [
            *state.get("steps", []),
            {
                "nodeId": "document_department",
                "status": "success",
                "message": "문서를 읽고 핵심 내용을 추출했습니다.",
            },
        ],
        "actions": [*state.get("actions", []), "문서 요약 검토", "후속 질문 정리"],
    }
