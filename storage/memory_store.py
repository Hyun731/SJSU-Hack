from schemas.workflow import WorkflowPlan, WorkflowRunResult


_workflow_plans: dict[str, WorkflowPlan] = {}
_run_results: dict[str, WorkflowRunResult] = {}
_connected_accounts: dict[str, dict] = {}
_run_counter = 0


def save_workflow(plan: WorkflowPlan) -> WorkflowPlan:
    _workflow_plans[plan.workflow_id] = plan
    return plan


def get_workflow(workflow_id: str) -> WorkflowPlan | None:
    return _workflow_plans.get(workflow_id)


def save_run(result: WorkflowRunResult) -> WorkflowRunResult:
    _run_results[result.run_id] = result
    return result


def get_run(run_id: str) -> WorkflowRunResult | None:
    return _run_results.get(run_id)


def save_connected_account(provider: str, account: dict) -> dict:
    _connected_accounts[provider] = account
    return account


def get_connected_account(provider: str) -> dict | None:
    return _connected_accounts.get(provider)


def next_run_id() -> str:
    global _run_counter
    _run_counter += 1
    return f"run_{_run_counter:03d}"
