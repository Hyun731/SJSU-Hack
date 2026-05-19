from uuid import uuid4

from schemas.workflow import (
    DepartmentNode,
    PrimeMinisterNode,
    ToolNode,
    TriggerNode,
    WorkflowEdge,
    WorkflowMetrics,
    WorkflowPlan,
)
from services.llm_service import OPENAI_MODEL, improve_workflow_copy, is_openai_enabled


MODEL_NAME = OPENAI_MODEL


def _workflow_id(kind: str) -> str:
    return f"wf_{kind}_{uuid4().hex[:10]}"


def _tool_status() -> str:
    return "connected" if is_openai_enabled() else "mock"


def _with_ai_copy(command: str, fallback: dict[str, str]) -> dict[str, str]:
    if not is_openai_enabled():
        return fallback
    return {**fallback, **improve_workflow_copy(command, fallback)}


def _prime_minister() -> PrimeMinisterNode:
    return PrimeMinisterNode(
        id="prime_minister",
        label="Prime Minister",
        role="Main Orchestrator",
        model=MODEL_NAME,
        instruction="사용자의 명령을 분석하고 필요한 부서에게 업무를 분배합니다.",
    )


def _trigger(trigger_id: str, trigger_type: str, label: str, description: str) -> TriggerNode:
    return TriggerNode(id=trigger_id, type=trigger_type, label=label, description=description)


def _email_department() -> DepartmentNode:
    return DepartmentNode(
        id="email_department",
        name="Email Department",
        role="새 이메일을 읽고 중요도를 분류합니다.",
        model=MODEL_NAME,
        tools=[
            ToolNode(id="gmail_reader", name="Gmail Reader", type="gmail", status="mock"),
            ToolNode(
                id="importance_filter",
                name="Importance Filter",
                type="classifier",
                status=_tool_status(),
            ),
        ],
    )


def _summary_department(role: str = "중요 내용을 짧게 요약합니다.") -> DepartmentNode:
    return DepartmentNode(
        id="summary_department",
        name="Summary Department",
        role=role,
        model=MODEL_NAME,
        tools=[ToolNode(id="summarizer", name="Summarizer", type="llm", status=_tool_status())],
    )


def _document_department() -> DepartmentNode:
    return DepartmentNode(
        id="document_department",
        name="Document Department",
        role="문서를 읽고 핵심 내용을 추출합니다.",
        model=MODEL_NAME,
        tools=[
            ToolNode(id="document_parser", name="Document Parser", type="parser", status=_tool_status())
        ],
    )


def _research_department() -> DepartmentNode:
    return DepartmentNode(
        id="research_department",
        name="Research Department",
        role="뉴스와 공개 정보를 조사합니다.",
        model=MODEL_NAME,
        tools=[ToolNode(id="news_researcher", name="News Researcher", type="search", status="mock")],
    )


def _report_department() -> DepartmentNode:
    return DepartmentNode(
        id="report_department",
        name="Report Department",
        role="최종 보고서를 사용자에게 전달합니다.",
        model=MODEL_NAME,
        tools=[
            ToolNode(
                id="dashboard_notification",
                name="Dashboard Notification",
                type="notification",
                status=_tool_status(),
            )
        ],
    )


def _is_automation(command: str) -> bool:
    return any(keyword in command for keyword in ["앞으로", "오면", "매일", "매주", "자동"])


def _build_edges(trigger: TriggerNode | None, departments: list[DepartmentNode]) -> list[WorkflowEdge]:
    edges: list[WorkflowEdge] = []
    previous = "prime_minister"
    if trigger:
        edges.append(WorkflowEdge(source=trigger.id, target="prime_minister"))

    for department in departments:
        edges.append(WorkflowEdge(source=previous, target=department.id))
        previous = department.id

    return edges


def create_workflow_plan(command: str) -> WorkflowPlan:
    command_lower = command.lower()
    mode = "automation" if _is_automation(command_lower) else "manual"
    trigger = None

    if any(keyword in command_lower for keyword in ["메일", "이메일", "email"]):
        if mode == "automation":
            trigger = _trigger(
                "trigger_gmail_new_email",
                "gmail.new_email",
                "Gmail Trigger",
                "새 이메일이 도착하면 워크플로우를 시작합니다.",
            )
        departments = [
            _email_department(),
            _summary_department("중요 이메일을 짧게 요약합니다."),
            _report_department(),
        ]
        copy = _with_ai_copy(
            command,
            {
                "title": "Important Email Summary Automation"
                if mode == "automation"
                else "Important Email Summary Workflow",
                "description": "새 이메일이 도착하면 중요도를 판단하고 요약해서 사용자에게 보고합니다.",
                "primeMinisterMessage": "Gmail 트리거를 생성하고 이메일관리부, 요약부, 보고부를 배치했습니다."
                if mode == "automation"
                else "이메일관리부, 요약부, 보고부를 배치했습니다.",
            },
        )
        return WorkflowPlan(
            workflowId=_workflow_id("email_summary"),
            title=copy["title"],
            description=copy["description"],
            mode=mode,
            trigger=trigger,
            primeMinister=PrimeMinisterNode(
                id="prime_minister",
                label="Prime Minister",
                role="Main Orchestrator",
                model=MODEL_NAME,
                instruction="이메일을 분석하고 필요한 부서에게 업무를 분배합니다.",
            ),
            departments=departments,
            edges=_build_edges(trigger, departments),
            metrics=WorkflowMetrics(
                estimatedCostUsd=0.03,
                estimatedTokens=3200,
                estimatedExecutionTimeSec=12,
            ),
            primeMinisterMessage=copy["primeMinisterMessage"],
        )

    if "문서" in command_lower:
        if mode == "automation":
            trigger = _trigger(
                "trigger_document_uploaded",
                "document.uploaded",
                "Document Trigger",
                "문서가 업로드되면 워크플로우를 시작합니다.",
            )
        departments = [_document_department(), _summary_department(), _report_department()]
        copy = _with_ai_copy(
            command,
            {
                "title": "Document Summary Workflow",
                "description": "문서를 분석하고 핵심 내용을 요약해서 보고합니다.",
                "primeMinisterMessage": "문서관리부, 요약부, 보고부를 배치했습니다.",
            },
        )
        return WorkflowPlan(
            workflowId=_workflow_id("document_summary"),
            title=copy["title"],
            description=copy["description"],
            mode=mode,
            trigger=trigger,
            primeMinister=_prime_minister(),
            departments=departments,
            edges=_build_edges(trigger, departments),
            metrics=WorkflowMetrics(
                estimatedCostUsd=0.02,
                estimatedTokens=2400,
                estimatedExecutionTimeSec=8,
            ),
            primeMinisterMessage=copy["primeMinisterMessage"],
        )

    if "뉴스" in command_lower:
        if mode == "automation":
            trigger = _trigger(
                "trigger_daily_news",
                "schedule.daily",
                "Daily News Trigger",
                "정해진 시간마다 뉴스 리서치를 시작합니다.",
            )
        departments = [_research_department(), _summary_department(), _report_department()]
        copy = _with_ai_copy(
            command,
            {
                "title": "Daily News Briefing Workflow",
                "description": "관심 주제의 뉴스를 조사하고 핵심 내용을 요약해 보고합니다.",
                "primeMinisterMessage": "리서치부, 요약부, 보고부를 배치했습니다.",
            },
        )
        return WorkflowPlan(
            workflowId=_workflow_id("daily_news"),
            title=copy["title"],
            description=copy["description"],
            mode=mode,
            trigger=trigger,
            primeMinister=_prime_minister(),
            departments=departments,
            edges=_build_edges(trigger, departments),
            metrics=WorkflowMetrics(
                estimatedCostUsd=0.04,
                estimatedTokens=3800,
                estimatedExecutionTimeSec=15,
            ),
            primeMinisterMessage=copy["primeMinisterMessage"],
        )

    departments = [_summary_department("사용자 요청을 정리하고 실행 가능한 형태로 요약합니다."), _report_department()]
    copy = _with_ai_copy(
        command,
        {
            "title": "Generic Royal Request Workflow",
            "description": "사용자의 요청을 정리하고 실행 가능한 보고서로 반환합니다.",
            "primeMinisterMessage": "요약부와 보고부를 배치했습니다.",
        },
    )
    return WorkflowPlan(
        workflowId=_workflow_id("generic_manual"),
        title=copy["title"],
        description=copy["description"],
        mode=mode,
        trigger=trigger,
        primeMinister=_prime_minister(),
        departments=departments,
        edges=_build_edges(trigger, departments),
        metrics=WorkflowMetrics(
            estimatedCostUsd=0.01,
            estimatedTokens=1200,
            estimatedExecutionTimeSec=5,
        ),
        primeMinisterMessage=copy["primeMinisterMessage"],
    )


def prime_minister_planner(state: dict) -> dict:
    return {**state, "plan": create_workflow_plan(state["command"])}


def prime_minister_execute_node(state: dict) -> dict:
    return {
        **state,
        "steps": state.get("steps", []),
        "actions": state.get("actions", []),
        "source_text": state.get("input", {}).get("text", ""),
    }
