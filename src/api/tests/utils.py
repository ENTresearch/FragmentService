import os
from supabase import create_client, Client as SupabaseClient
from pydantic import BaseModel


class User(BaseModel):
    login: str
    password: str
    api_key: str

def get_test_users() -> tuple[User, User]:
    """ Return the test users from the environment (user, admin) """
    user = User(
        login = os.getenv("USER_LOGIN"),
        password = os.getenv("USER_PASSWORD"),
        api_key = os.getenv("USER_API_KEY")
    )

    admin = User(
        login = os.getenv("ADMIN_LOGIN"),
        password = os.getenv("ADMIN_PASSWORD"),
        api_key = os.getenv("ADMIN_API_KEY")
    )
    return user, admin

def init_supabase() -> SupabaseClient:
    """ Initialize Supabase client based on the environment variables """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    supabase: SupabaseClient = create_client(url, key)
    return supabase

def sign_in_to_supabase(supabase: SupabaseClient, user: User) -> str:
    """ Sign in to Supabase and return the access JWT """
    response = supabase.auth.sign_in_with_password(
        {"email": user.login, "password": user.password}
    )
    return response.session.access_token

def get_auth_headers(supabase: SupabaseClient, user: User) -> dict:
    """ Get the authentication headers for the user """
    token = sign_in_to_supabase(supabase, user)
    return {
            "Authorization": "Bearer " + token,
            "apikey": user.api_key
        }