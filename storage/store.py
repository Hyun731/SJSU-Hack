from schemas.workflow import WorkflowPlan, WorkflowRunResult
from services.supabase_client import is_supabase_enabled
from storage import memory_store, supabase_store


def storage_backend_name() -> str:
    return "supabase" if is_supabase_enabled() else "memory"


def save_workflow(plan: WorkflowPlan) -> WorkflowPlan:
    if is_supabase_enabled():
        return supabase_store.save_workflow(plan)
    return memory_store.save_workflow(plan)


def get_workflow(workflow_id: str) -> WorkflowPlan | None:
    if is_supabase_enabled():
        return supabase_store.get_workflow(workflow_id)
    return memory_store.get_workflow(workflow_id)


def save_run(result: WorkflowRunResult, input_data: dict | None = None) -> WorkflowRunResult:
    if is_supabase_enabled():
        return supabase_store.save_run(result, input_data=input_data)
    return memory_store.save_run(result)


def get_run(run_id: str) -> WorkflowRunResult | None:
    if is_supabase_enabled():
        return supabase_store.get_run(run_id)
    return memory_store.get_run(run_id)


def save_connected_account(provider: str, account: dict) -> dict:
    if is_supabase_enabled():
        return supabase_store.save_connected_account(provider, account)
    return memory_store.save_connected_account(provider, account)


def get_connected_account(provider: str) -> dict | None:
    if is_supabase_enabled():
        return supabase_store.get_connected_account(provider)
    return memory_store.get_connected_account(provider)


def delete_connected_account(provider: str) -> None:
    if is_supabase_enabled():
        supabase_store.delete_connected_account(provider)
        return
    memory_store.delete_connected_account(provider)
