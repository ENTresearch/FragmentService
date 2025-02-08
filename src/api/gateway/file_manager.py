import os
from fastapi import HTTPException

UPLOAD_DIR = os.getenv('UPLOAD_DIR')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_fragment_file(user_id, recording_id, index, extension, file):
    path = os.path.join(UPLOAD_DIR, str(user_id), str(recording_id))
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, f"{index}.{extension}")
    with open(file_path, "wb") as f:
        f.write(file.file.read())

def get_fragment_file(user_id, recording_id, index, extension):
    file_path = os.path.join(UPLOAD_DIR, str(user_id), str(recording_id), f"{index}.{extension}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return file_path

def delete_fragment_file(user_id, recording_id, index, extension):
    file_path = os.path.join(UPLOAD_DIR, str(user_id), str(recording_id), f"{index}.{extension}")
    if os.path.exists(file_path):
        os.remove(file_path)