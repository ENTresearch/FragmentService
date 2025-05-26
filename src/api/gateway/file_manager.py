import os
from fastapi import HTTPException
from fastapi.responses import FileResponse
import hashlib
import shutil

UPLOAD_DIR = os.getenv('UPLOAD_DIR')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_fragment_file(user_id, recording_id, index, extension, file):
    path = os.path.join(UPLOAD_DIR, str(user_id), str(recording_id))
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, f"{index}.{extension}")
    file.file.seek(0)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

def get_fragment_file_path(user_id, recording_id, index, extension):
    file_path = os.path.join(UPLOAD_DIR, str(user_id), str(recording_id), f"{index}.{extension}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return file_path

def delete_fragment_file(user_id, recording_id, index, extension):
    file_path = os.path.join(UPLOAD_DIR, str(user_id), str(recording_id), f"{index}.{extension}")
    if os.path.exists(file_path):
        os.remove(file_path)

def delete_recording_files(user_id, recording_id):
    path = os.path.join(UPLOAD_DIR, str(user_id), str(recording_id))
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Recording not found")
    shutil.rmtree(path)

def _calculate_md5(fileobj):
    """Calculate MD5 checksum from file-like object (fileobj must be at position 0)."""
    md5 = hashlib.md5()
    for chunk in iter(lambda: fileobj.read(4096), b""):
        md5.update(chunk)
    fileobj.seek(0)
    return md5.hexdigest()

def calculate_md5(source):
    """
    Calculate MD5 checksum from file path or file-like object.
    If source is a string, treat as file path. Otherwise, treat as file-like object.
    """
    if isinstance(source, str):
        with open(source, "rb") as f:
            return _calculate_md5(f)
    else:
        return _calculate_md5(source)

def verify_md5(fileobj, expected_md5):
    """Compare MD5 checksum of file-like object with expected MD5."""
    actual_md5 = calculate_md5(fileobj)
    if expected_md5:
        if actual_md5 != expected_md5:
            raise HTTPException(status_code=400, detail="MD5 checksum mismatch")
    return actual_md5

def file_response_with_md5(file_path: str, filename: str):
    """Return a file response with MD5 checksum in headers."""
    md5 = calculate_md5(file_path)
    headers = {"X-Content-MD5": md5}
    return FileResponse(
        file_path,
        filename=filename,
        headers=headers
    )