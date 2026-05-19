from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class PlanWorkflowRequest(CamelModel):
    command: str


class RunWorkflowRequest(CamelModel):
    workflow_id: str = Field(alias="workflowId")
    input: dict[str, Any] = Field(default_factory=dict)


class ToolNode(CamelModel):
    id: str
    name: str
    type: str
    status: Literal["mock", "connected"] = "mock"


class TriggerNode(CamelModel):
    id: str
    type: str
    label: str
    description: str


class PrimeMinisterNode(CamelModel):
    id: str
    label: str
    role: str
    model: str
    instruction: str


class DepartmentNode(CamelModel):
    id: str
    name: str
    role: str
    model: str
    tools: list[ToolNode] = Field(default_factory=list)


class WorkflowEdge(CamelModel):
    source: str
    target: str


class WorkflowMetrics(CamelModel):
    estimated_cost_usd: float | None = Field(default=None, alias="estimatedCostUsd")
    estimated_tokens: int | None = Field(default=None, alias="estimatedTokens")
    estimated_execution_time_sec: int | None = Field(
        default=None, alias="estimatedExecutionTimeSec"
    )
    actual_cost_usd: float | None = Field(default=None, alias="actualCostUsd")
    actual_tokens: int | None = Field(default=None, alias="actualTokens")
    execution_time_sec: int | None = Field(default=None, alias="executionTimeSec")


class WorkflowPlan(CamelModel):
    workflow_id: str = Field(alias="workflowId")
    title: str
    description: str
    mode: Literal["automation", "manual"]
    trigger: TriggerNode | None = None
    prime_minister: PrimeMinisterNode = Field(alias="primeMinister")
    departments: list[DepartmentNode]
    edges: list[WorkflowEdge]
    metrics: WorkflowMetrics
    prime_minister_message: str = Field(alias="primeMinisterMessage")


class WorkflowRunStep(CamelModel):
    node_id: str = Field(alias="nodeId")
    status: Literal["success", "error"]
    message: str


class RoyalReport(CamelModel):
    title: str
    summary: str
    actions: list[str] = Field(default_factory=list)


class WorkflowRunResult(CamelModel):
    run_id: str = Field(alias="runId")
    workflow_id: str = Field(alias="workflowId")
    status: Literal["success", "error"]
    steps: list[WorkflowRunStep]
    report: RoyalReport
    metrics: WorkflowMetrics
