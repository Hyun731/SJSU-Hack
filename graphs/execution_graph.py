from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from nodes.document_department import document_department_node
from nodes.email_department import email_department_node
from nodes.prime_minister import prime_minister_execute_node
from nodes.report_department import report_department_node
from nodes.research_department import research_department_node
from nodes.summary_department import summary_department_node
from schemas.workflow import RoyalReport, WorkflowMetrics, WorkflowPlan, WorkflowRunResult


class ExecutionState(TypedDict, total=False):
    workflow: WorkflowPlan
    workflow_id: str
    input: dict[str, Any]
    steps: list[dict[str, str]]
    actions: list[str]
    source_text: str
    email: dict[str, Any]
    document: dict[str, Any]
    research_findings: list[str]
    importance: str
    summary: str
    report: dict[str, Any]


def _department_ids(state: ExecutionState) -> set[str]:
    return {department.id for department in state["workflow"].departments}


def _route_first_department(state: ExecutionState) -> str:
    department_ids = _department_ids(state)
    if "email_department" in department_ids:
        return "email_department"
    if "document_department" in department_ids:
        return "document_department"
    if "research_department" in department_ids:
        return "research_department"
    return "summary_department"


def build_execution_graph():
    graph = StateGraph(ExecutionState)
    graph.add_node("prime_minister_execute", prime_minister_execute_node)
    graph.add_node("email_department", email_department_node)
    graph.add_node("document_department", document_department_node)
    graph.add_node("research_department", research_department_node)
    graph.add_node("summary_department", summary_department_node)
    graph.add_node("report_department", report_department_node)

    graph.add_edge(START, "prime_minister_execute")
    graph.add_conditional_edges(
        "prime_minister_execute",
        _route_first_department,
        {
            "email_department": "email_department",
            "document_department": "document_department",
            "research_department": "research_department",
            "summary_department": "summary_department",
        },
    )
    graph.add_edge("email_department", "summary_department")
    graph.add_edge("document_department", "summary_department")
    graph.add_edge("research_department", "summary_department")
    graph.add_edge("summary_department", "report_department")
    graph.add_edge("report_department", END)
    return graph.compile()


execution_graph = build_execution_graph()


def run_workflow(workflow: WorkflowPlan, input_data: dict[str, Any]) -> WorkflowRunResult:
    final_state: ExecutionState = execution_graph.invoke(
        {
            "workflow": workflow,
            "workflow_id": workflow.workflow_id,
            "input": input_data,
            "steps": [],
            "actions": [],
        }
    )

    return WorkflowRunResult(
        runId=f"run_{uuid4().hex[:12]}",
        workflowId=workflow.workflow_id,
        status="error"
        if any(step.get("status") == "error" for step in final_state.get("steps", []))
        else "success",
        steps=final_state.get("steps", []),
        report=RoyalReport(**final_state["report"]),
        metrics=WorkflowMetrics(actualCostUsd=0.01, actualTokens=1100, executionTimeSec=4),
    )
