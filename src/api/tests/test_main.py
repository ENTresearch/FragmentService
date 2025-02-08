from fastapi.testclient import TestClient
from gateway.main import app
from tests.utils import get_auth_headers, get_test_users, init_supabase, User
from supabase import Client as SupabaseClient

client = TestClient(app)
user, admin = get_test_users()
supabase: SupabaseClient = init_supabase()

### Unit tests for testing the inner workings of the API endpoints and comparing it against expected results
### These tests do not test the SSL/TLS layer - integration tests should be implemented in the future

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_recording_creation():
    response = client.post(
        "/recordings",
        headers=get_auth_headers(supabase, user),
        json={
            "sample_rate": 44100,
            "channel_count": 2,
            "file_extension": "wav"
        }
    )
    #print (response.json())
    assert response.status_code == 201
    assert response.json().get('sample_rate') == 44100

def test_recordings_list():
    response = client.get(
        "/recordings",
        headers=get_auth_headers(supabase, user)
    )
    #print (response.json())
    assert response.status_code == 200
    assert isinstance(response.json(), list)