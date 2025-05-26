from fastapi.testclient import TestClient
from gateway.main import app
from tests.utils import User, get_auth_headers, get_test_users, init_supabase, md5_of_bytes, get_test_file_bytes
from supabase import Client as SupabaseClient
import io

client = TestClient(app)
user, admin = get_test_users()
supabase: SupabaseClient = init_supabase()
TEST_FILE_PATH = "/app/tests/test.flac"

### Unit tests for testing the inner workings of the API endpoints and comparing it against expected results
### These tests do not test the SSL/TLS layer - integration tests should be implemented in the future

def test_public_recording_and_fragment_crud():
    # CREATE recording
    user_headers = get_auth_headers(supabase, user)
    resp = client.post("/recordings", headers=user_headers, json={
        "sample_rate": 48000, "channel_count": 1, "file_extension": "flac"
    })
    assert resp.status_code == 201
    rec = resp.json()
    recording_id = rec["id"]

    # LIST recordings
    resp = client.get("/recordings", headers=user_headers)
    assert resp.status_code == 200
    assert any(r["id"] == recording_id for r in resp.json())

    # GET recording
    resp = client.get(f"/recordings/{recording_id}", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == recording_id

    # UPLOAD fragments
    data = get_test_file_bytes(TEST_FILE_PATH)
    md5 = md5_of_bytes(data)
    # with MD5
    resp = client.post(
        f"/recordings/{recording_id}/fragments",
        headers=user_headers,
        files={"file": (TEST_FILE_PATH, io.BytesIO(data), "audio/flac")},
        data={"index": "0", "sample_number": "0", "md5_checksum": md5}
    )
    assert resp.status_code == 201
    # without MD5
    resp = client.post(
        f"/recordings/{recording_id}/fragments",
        headers=user_headers,
        files={"file": (TEST_FILE_PATH, io.BytesIO(data), "audio/flac")},
        data={"index": "1", "sample_number": "1"}
    )
    assert resp.status_code == 201

    # GET fragment metadata
    resp = client.get(f"/recordings/{recording_id}/fragments/0", headers=user_headers)
    assert resp.status_code == 200
    meta = resp.json()
    assert meta["index"] == 0 and meta["sample_number"] == 0

    # DOWNLOAD fragment file and check MD5
    resp = client.get(f"/recordings/{recording_id}/fragments/0/file", headers=user_headers)
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-MD5") == md5_of_bytes(resp.content)

    # DELETE fragment
    resp = client.delete(f"/recordings/{recording_id}/fragments/1", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Fragment deleted")

    # DELETE recording
    resp = client.delete(f"/recordings/{recording_id}", headers=user_headers)
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"]

def test_admin_full_crud_flow():
    admin_headers = get_auth_headers(supabase, admin)
    # LIST all recordings (should include at least public ones)
    resp = client.get("/admin/recordings", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # CREATE recording for test user
    resp = client.post(
        f"/admin/users/{user.id}/recordings",
        headers=admin_headers,
        json={"sample_rate": 44100, "channel_count": 2, "file_extension": "flac"}
    )
    assert resp.status_code == 201
    rec = resp.json()
    admin_rec_id = rec["id"]

    # LIST recordings of that user
    resp = client.get(f"/admin/users/{user.id}", headers=admin_headers)
    assert resp.status_code == 200
    assert any(r["id"] == admin_rec_id for r in resp.json())

    # GET single recording as admin
    resp = client.get(f"/admin/recordings/{admin_rec_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == admin_rec_id

    # UPDATE recording metadata
    resp = client.put(
        f"/admin/recordings/{admin_rec_id}",
        headers=admin_headers,
        json={"sample_rate": 22050, "channel_count": 2, "file_extension": "flac"}
    )
    assert resp.status_code == 200
    assert resp.json()["sample_rate"] == 22050

    # UPLOAD fragments as admin
    data = get_test_file_bytes(TEST_FILE_PATH)
    md5 = md5_of_bytes(data)
    resp = client.post(
        f"/admin/users/{user.id}/recordings/{admin_rec_id}/fragments",
        headers=admin_headers,
        files={"file": (TEST_FILE_PATH, io.BytesIO(data), "audio/flac")},
        data={"index": "0", "sample_number": "5", "md5_checksum": md5}
    )
    assert resp.status_code == 201
    # GET fragment file
    resp = client.get(f"/admin/recordings/{admin_rec_id}/fragments/0/file", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-MD5") == md5_of_bytes(resp.content)

    ### TODO: Fix update fragment metadata
    """ # UPDATE fragment metadata
    resp = client.put(
        f"/admin/recordings/{admin_rec_id}/fragments/0",
        headers=admin_headers,
        json={"sample_number": 99}
    )
    assert resp.status_code == 200
    assert resp.json()["sample_number"] == 99 """

    # DELETE fragment and recording
    resp = client.delete(f"/admin/recordings/{admin_rec_id}/fragments/0", headers=admin_headers)
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"]

    resp = client.delete(f"/admin/recordings/{admin_rec_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"]