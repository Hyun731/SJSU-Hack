# oh-my-kingdom Backend MVP

FastAPI backend for a no-code AI orchestration MVP using LangGraph.

The product metaphor:

- User: King
- Main orchestrator AI: Prime Minister
- Specialized workflow units: Departments
- Concrete integrations/functions: Tools
- Trigger: Event that starts a workflow
- Final output: Royal Report

This MVP uses mock external integrations. Workflow plans and runs can be stored in Supabase when configured, or in memory when Supabase environment variables are missing.

## Install

```bash
cd backend
pip install -r requirements.txt
```

## Configure OpenAI

Create a local `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

`OPENAI_API_KEY` is required for workflow planning and execution. The backend uses the OpenAI Responses API for workflow copy, importance classification, summaries, and Royal Reports. If the key is missing, `/api/workflows/plan` and `/api/workflows/run` return an error instead of silently using mock AI output.

## Configure Supabase

Create a Supabase project, then open Project Settings > API and copy:

- Project URL
- anon or publishable key
- service_role key

Add them to `.env`:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-or-publishable-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Keep `SUPABASE_SERVICE_ROLE_KEY` on the backend only. Never expose it in the frontend.

In the Supabase Dashboard, open SQL Editor and run the schema in:

```text
backend/db/schema.sql
```

The schema creates:

- `workflows`: saved workflow plans
- `workflow_runs`: saved run results
- `connected_accounts`: future Gmail/Google OAuth token storage

If Supabase variables are not configured, the backend automatically falls back to in-memory storage.

## Configure Gmail OAuth

Create OAuth credentials in Google Cloud Console:

1. Open Google Cloud Console.
2. Create or select a project.
3. Enable the Gmail API.
4. Configure the OAuth consent screen.
5. Create an OAuth Client ID for a web application.
6. Add this authorized redirect URI:

```text
http://localhost:8000/api/integrations/google/callback
```

Add the credentials to `.env`:

```bash
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/integrations/google/callback
```

The backend requests these scopes:

```text
openid email profile https://www.googleapis.com/auth/gmail.readonly
```

This lets the backend read Gmail messages but not modify or send email.

## Run

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## Curl Examples

### 1. Health check

```bash
curl http://localhost:8000/health
```

Check OpenAI mode:

```bash
curl http://localhost:8000/api/ai/status
```

Check storage mode:

```bash
curl http://localhost:8000/api/storage/status
```

Check Gmail integration:

```bash
curl http://localhost:8000/api/integrations/google/status
```

Get the Google OAuth URL:

```bash
curl http://localhost:8000/api/integrations/google/auth-url
```

Open the returned `url` in your browser and approve Google access. After the callback completes, test the latest Gmail read:

```bash
curl http://localhost:8000/api/integrations/gmail/latest
```

### 2. Plan email workflow

```bash
curl -X POST http://localhost:8000/api/workflows/plan \
  -H "Content-Type: application/json" \
  -d '{
    "command": "앞으로 중요한 이메일이 오면 요약해서 알려줘"
  }'
```

### 3. Run email workflow

Create the plan first, copy the returned `workflowId`, then run:

```bash
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{
    "workflowId": "wf_email_summary_abc123",
    "input": {
      "sampleEmailText": "내일 오후 3시에 회의 가능하신가요? 발표 자료도 함께 확인 부탁드립니다."
    }
  }'
```

To run against your latest real Gmail message instead of sample text:

```bash
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{
    "workflowId": "wf_email_summary_abc123",
    "input": {
      "useLatestGmail": true
    }
  }'
```

## Architecture Summary

- `main.py`: FastAPI app, CORS, and API routes.
- `schemas/workflow.py`: Pydantic request and response contracts.
- `graphs/planner_graph.py`: LangGraph planner graph.
- `graphs/execution_graph.py`: LangGraph mock execution graph.
- `nodes/`: Prime Minister and Department node functions.
- `tools/mock_tools.py`: Mock email, summary, document, research, and report tools.
- `services/llm_service.py`: OpenAI Responses API wrapper.
- `services/gmail_service.py`: Google OAuth and Gmail readonly API helper.
- `services/supabase_client.py`: Supabase client configuration.
- `storage/memory_store.py`: In-memory workflow and run storage fallback.
- `storage/supabase_store.py`: Supabase workflow and run storage.
- `storage/store.py`: Storage facade that chooses Supabase or memory.
- `db/schema.sql`: Database schema for the MVP.

Planning is deterministic for MVP:

- Email commands create an email summary workflow.
- Document commands create a document summary workflow.
- News commands create a daily news workflow.
- Unknown commands create a generic manual workflow.
- Automation keywords such as `앞으로`, `오면`, `매일`, `매주`, or `자동` set `mode` to `automation`.

## MVP Limitations

- Data is stored in Supabase when configured. Otherwise, memory storage resets when the server restarts.
- Gmail, Calendar, Slack, and news search integrations are mocked.
- Gmail can read the latest inbox message after OAuth connection, but automatic push/polling is not implemented yet.
- OpenAI is used only for text reasoning/generation when `OPENAI_API_KEY` is configured.
- No app-level authentication or authorization yet.
- No real Calendar, Slack, or background worker calls.
- No background workers or scheduled execution.
# SJSU-Hack
