create extension if not exists pgcrypto;

create table if not exists public.workflows (
  id text primary key,
  user_id uuid null,
  title text not null,
  description text not null,
  mode text not null check (mode in ('automation', 'manual')),
  plan jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.workflow_runs (
  id text primary key,
  workflow_id text not null references public.workflows(id) on delete cascade,
  status text not null,
  input jsonb not null default '{}'::jsonb,
  result jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.connected_accounts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid null,
  provider text not null,
  provider_email text null,
  access_token text null,
  refresh_token text null,
  scopes text[] not null default '{}',
  token_expires_at timestamptz null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.connected_accounts
  add column if not exists token_expires_at timestamptz null;

create index if not exists workflow_runs_workflow_id_idx
  on public.workflow_runs(workflow_id);

create index if not exists connected_accounts_provider_idx
  on public.connected_accounts(provider);

create unique index if not exists connected_accounts_provider_unique_idx
  on public.connected_accounts(provider);
