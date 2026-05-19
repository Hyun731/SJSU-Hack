from schemas.workflow import WorkflowPlan, WorkflowRunResult
from services.supabase_client import get_supabase_client


def save_workflow(plan: WorkflowPlan) -> WorkflowPlan:
    client = get_supabase_client()
    payload = {
        "id": plan.workflow_id,
        "title": plan.title,
        "description": plan.description,
        "mode": plan.mode,
        "plan": plan.model_dump(by_alias=True, exclude_none=True),
    }
    client.table("workflows").upsert(payload).execute()
    return plan


def get_workflow(workflow_id: str) -> WorkflowPlan | None:
    client = get_supabase_client()
    response = client.table("workflows").select("plan").eq("id", workflow_id).limit(1).execute()
    if not response.data:
        return None
    return WorkflowPlan.model_validate(response.data[0]["plan"])


def save_run(result: WorkflowRunResult, input_data: dict | None = None) -> WorkflowRunResult:
    client = get_supabase_client()
    payload = {
        "id": result.run_id,
        "workflow_id": result.workflow_id,
        "status": result.status,
        "input": input_data or {},
        "result": result.model_dump(by_alias=True, exclude_none=True),
    }
    client.table("workflow_runs").upsert(payload).execute()
    return result


def get_run(run_id: str) -> WorkflowRunResult | None:
    client = get_supabase_client()
    response = client.table("workflow_runs").select("result").eq("id", run_id).limit(1).execute()
    if not response.data:
        return None
    return WorkflowRunResult.model_validate(response.data[0]["result"])


def save_connected_account(provider: str, account: dict) -> dict:
    client = get_supabase_client()
    existing = (
        client.table("connected_accounts")
        .select("id")
        .eq("provider", provider)
        .limit(1)
        .execute()
    )
    payload = {"provider": provider, **account}

    if existing.data:
        account_id = existing.data[0]["id"]
        client.table("connected_accounts").update(payload).eq("id", account_id).execute()
    else:
        client.table("connected_accounts").insert(payload).execute()

    return payload


def get_connected_account(provider: str) -> dict | None:
    client = get_supabase_client()
    response = (
        client.table("connected_accounts")
        .select("*")
        .eq("provider", provider)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return response.data[0]


def delete_connected_account(provider: str) -> None:
    client = get_supabase_client()
    client.table("connected_accounts").delete().eq("provider", provider).execute()
