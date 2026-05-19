from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from nodes.prime_minister import prime_minister_planner
from schemas.workflow import WorkflowPlan


class PlannerState(TypedDict, total=False):
    command: str
    plan: WorkflowPlan


def build_planner_graph():
    graph = StateGraph(PlannerState)
    graph.add_node("prime_minister_planner", prime_minister_planner)
    graph.add_edge(START, "prime_minister_planner")
    graph.add_edge("prime_minister_planner", END)
    return graph.compile()


planner_graph = build_planner_graph()


def plan_workflow(command: str) -> WorkflowPlan:
    result: dict[str, Any] = planner_graph.invoke({"command": command})
    return result["plan"]
