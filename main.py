from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from graphs.execution_graph import run_workflow
from graphs.planner_graph import plan_workflow
from schemas.workflow import PlanWorkflowRequest, RunWorkflowRequest, WorkflowPlan, WorkflowRunResult
from services.gmail_service import (
    build_google_auth_url,
    disconnect_google_account,
    exchange_google_code,
    FRONTEND_URL,
    gmail_connection_status,
    is_gmail_connected,
    is_google_oauth_configured,
    read_latest_email,
)
from services.llm_service import OPENAI_MODEL, is_openai_enabled
from storage.store import get_workflow, save_run, save_workflow, storage_backend_name


app = FastAPI(title="oh-my-kingdom backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "oh-my-kingdom-backend"}


@app.get("/api/ai/status")
def ai_status() -> dict[str, str | bool]:
    return {
        "enabled": is_openai_enabled(),
        "provider": "openai",
        "model": OPENAI_MODEL,
    }


@app.get("/api/storage/status")
def storage_status() -> dict[str, str]:
    return {"backend": storage_backend_name()}


def ensure_openai_ready() -> None:
    if not is_openai_enabled():
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is required for workflow planning and execution.",
        )


@app.get("/api/integrations/google/status")
def google_status() -> dict[str, Any]:
    return gmail_connection_status()


@app.get("/api/integrations/google/auth-url")
def google_auth_url() -> dict[str, str]:
    try:
        return {"url": build_google_auth_url()}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/integrations/google/callback")
def google_callback(code: str):
    try:
        exchange_google_code(code)
        return RedirectResponse(url=f"{FRONTEND_URL}/?gmail=connected", status_code=302)
    except Exception as exc:
        return RedirectResponse(url=f"{FRONTEND_URL}/?gmail=error", status_code=302)


@app.delete("/api/integrations/google")
def google_disconnect() -> dict[str, str]:
    disconnect_google_account()
    return {"status": "disconnected"}


@app.get("/api/integrations/gmail/latest")
def gmail_latest() -> dict:
    try:
        return read_latest_email()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read Gmail: {exc}") from exc


@app.post(
    "/api/workflows/plan",
    response_model=WorkflowPlan,
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def create_workflow_plan(request: PlanWorkflowRequest) -> WorkflowPlan:
    ensure_openai_ready()
    try:
        plan = plan_workflow(request.command)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI planning failed: {exc}") from exc
    save_workflow(plan)
    return plan


@app.post(
    "/api/workflows/run",
    response_model=WorkflowRunResult,
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
def execute_workflow(request: RunWorkflowRequest) -> WorkflowRunResult:
    ensure_openai_ready()
    workflow = get_workflow(request.workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{request.workflow_id}' was not found. Create a plan first.",
        )

    try:
        result = run_workflow(workflow, request.input)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI execution failed: {exc}") from exc
    save_run(result, input_data=request.input)
    return result
