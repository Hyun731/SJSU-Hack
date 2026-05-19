import os

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def is_supabase_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_client():
    if not is_supabase_enabled():
        raise RuntimeError("Supabase is not configured.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
