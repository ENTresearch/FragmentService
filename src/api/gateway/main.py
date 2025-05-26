from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from gateway.database import get_db
from gateway.auth import verify_jwt, verify_api_key, verify_admin_jwt, verify_admin_api_key
from gateway.models import Recording, Fragment
from gateway.schemas import RecordingCreate, FragmentCreate
from gateway.file_manager import delete_recording_files, delete_user_directory, save_fragment_file, get_fragment_file_path, delete_fragment_file, verify_md5, file_response_with_md5
from gateway.utils import get_admin_recording, get_fragment_in_recording, generate_api_key, generate_api_secret

import os
import uvicorn

app = FastAPI()# docs_url=None, redoc_url=None)

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.post("/recordings", status_code=status.HTTP_201_CREATED)
async def create_recording(recording: RecordingCreate, db: Session = Depends(get_db), user = Depends(verify_jwt), api_key: str = Depends(verify_api_key)):
    user_id = user["sub"]
    new_recording = Recording(owner_id=user_id, **recording.model_dump())
    db.add(new_recording)
    db.commit()
    db.refresh(new_recording)
    return new_recording

@app.post("/recordings/{recording_id}/fragments", status_code=status.HTTP_201_CREATED)
async def create_fragment(
    recording_id: str,
    index: str = Form(...),
    sample_number: str = Form(...),
    file: UploadFile = File(...),
    md5_checksum: str = Form(None),
    db: Session = Depends(get_db),
    user = Depends(verify_jwt),
    api_key: str = Depends(verify_api_key)
):
    user_id = user["sub"]
    recording = db.query(Recording).filter_by(id=recording_id, owner_id=user_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    verify_md5(file.file, md5_checksum)
    save_fragment_file(user_id, recording_id, index, recording.file_extension, file)
    new_fragment = Fragment(recording_id=recording_id, index=int(index), sample_number=int(sample_number))
    db.add(new_fragment)
    db.commit()
    db.refresh(new_fragment)
    return new_fragment

@app.get("/recordings")
async def list_recordings(db: Session = Depends(get_db), user = Depends(verify_jwt), api_key: str = Depends(verify_api_key)):
    user_id = user["sub"]
    recordings = (
        db.query(Recording)
        .filter_by(owner_id=user_id)
        .options(joinedload(Recording.fragments))
        .all()
    )
    return recordings

@app.get("/recordings/{recording_id}")
async def get_recording(recording_id: str, db: Session = Depends(get_db), user = Depends(verify_jwt), api_key = Depends(verify_api_key)):
    user_id = user["sub"]
    recording = (
        db.query(Recording)
        .filter_by(id=recording_id, owner_id=user_id)
        .options(joinedload(Recording.fragments))
        .first()
    )
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording

@app.get("/recordings/{recording_id}/fragments/{index}")
async def get_fragment_metadata(
    recording_id: str,
    index: int,
    db: Session = Depends(get_db),
    user = Depends(verify_jwt),
    api_key: str = Depends(verify_api_key),
):
    user_id = user["sub"]
    fragment, _ = get_fragment_in_recording(db, recording_id, index, user_id)

    return fragment

""" @app.get("/recordings/{recording_id}/fragments/{index}/file")
async def get_fragment_file(
    recording_id: str,
    index: int,
    db: Session = Depends(get_db),
    user = Depends(verify_jwt),
    api_key: str = Depends(verify_api_key),
):
    user_id = user["sub"]
    _, recording = get_fragment_in_recording(db, recording_id, index, user_id)
    
    file_path = get_fragment_file_path(
        user_id=user_id,
        recording_id=recording_id,
        index=index,
        extension=recording.file_extension,
    )
    
    return FileResponse(
        file_path,
        filename=f"{index}.{recording.file_extension}",
    ) """

@app.delete("/recordings/{recording_id}")
async def delete_recording(recording_id: str, db: Session = Depends(get_db), user = Depends(verify_jwt), api_key: str = Depends(verify_api_key)):
    user_id = user["sub"]
    recording = (
        db.query(Recording)
        .filter_by(id=recording_id, owner_id=user_id)
        .options(joinedload(Recording.fragments))
        .first()
    )
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    delete_recording_files(user_id, recording_id)
    db.delete(recording)
    db.commit()
    return {"message": "Recording and associated fragments deleted"}

@app.delete("/recordings/{recording_id}/fragments/{index}")
async def delete_fragment(recording_id: str, index: int, db: Session = Depends(get_db), user = Depends(verify_jwt), api_key: str = Depends(verify_api_key)):
    user_id = user["sub"]
    fragment, recording = get_fragment_in_recording(db, recording_id, index, user_id)
    delete_fragment_file(user_id, recording_id, index, recording.file_extension)
    db.delete(fragment)
    db.commit()
    return {"message": "Fragment deleted"}

### ADMIN ROUTES ###

admin_url = os.getenv("ADMIN_URL", "admin")

@app.get("/{admin_url}/recordings")
async def admin_list_all_recordings(db: Session = Depends(get_db), user: dict = Depends(verify_admin_jwt), api_key: str = Depends(verify_admin_api_key)):
    """ Returns metadata of all recordings from all users from the database """
    recordings = (
        db.query(Recording)
        .options(joinedload(Recording.fragments))
        .all()
    )
    return recordings

@app.get("/{admin_url}/users/{owner_id}")
async def admin_list_user_recordings(owner_id: str, db: Session = Depends(get_db), user: dict = Depends(verify_admin_jwt), api_key: str = Depends(verify_admin_api_key)):
    """ Returns metadata of all recordings created by a specific user from the database """
    recordings = (
        db.query(Recording)
        .filter_by(owner_id=owner_id)
        .options(joinedload(Recording.fragments))
        .all()
    )
    return recordings

@app.get("/{admin_url}/recordings/{recording_id}")
async def admin_get_recording(recording_id: str, db: Session = Depends(get_db), user: dict = Depends(verify_admin_jwt), api_key: str = Depends(verify_admin_api_key)):
    """ Returns metadata of a specific recording from the database """
    recording = (
        db.query(Recording)
        .filter_by(id=recording_id)
        .options(joinedload(Recording.fragments))
        .first()
    )
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording

@app.get("/{admin_url}/recordings/{recording_id}/fragments/{index}/file")
async def admin_get_fragment_file(
    recording_id: str,
    index: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_admin_jwt),
    api_key: str = Depends(verify_admin_api_key)
):
    recording = get_admin_recording(db, user, recording_id)

    fragment = (
        db.query(Fragment)
        .filter_by(recording_id=recording_id, index=index)
        .first()
    )
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")

    file_path = get_fragment_file_path(
        user_id=recording.owner_id,
        recording_id=recording_id,
        index=index,
        extension=recording.file_extension,
    )
    return file_response_with_md5(
        file_path,
        filename=f"{index}.{recording.file_extension}",
    )

@app.get("/recordings/{recording_id}/fragments/{index}/file")
async def get_fragment_file(
    recording_id: str,
    index: int,
    db: Session = Depends(get_db),
    user = Depends(verify_jwt),
    api_key: str = Depends(verify_api_key),
):
    user_id = user["sub"]
    _, recording = get_fragment_in_recording(db, recording_id, index, user_id)
    file_path = get_fragment_file_path(
        user_id=user_id,
        recording_id=recording_id,
        index=index,
        extension=recording.file_extension,
    )
    return file_response_with_md5(
        file_path,
        filename=f"{index}.{recording.file_extension}",
    )

@app.post("/{admin_url}/users/{owner_id}/recordings", status_code=status.HTTP_201_CREATED)
async def admin_create_recording(owner_id: str, recording: RecordingCreate, db: Session = Depends(get_db), user: dict = Depends(verify_admin_jwt), api_key: str = Depends(verify_admin_api_key)):
    """ Creates a new recording for a specific user """
    new_recording = Recording(owner_id=owner_id, **recording.model_dump())
    db.add(new_recording)
    db.commit()
    db.refresh(new_recording)
    return new_recording

@app.post("/{admin_url}/users/{owner_id}/recordings/{recording_id}/fragments", status_code=status.HTTP_201_CREATED)
async def admin_create_fragment(
    owner_id: str,
    recording_id: str,
    index: str = Form(...),
    sample_number: str = Form(...),
    file: UploadFile = File(...),
    md5_checksum: str = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_admin_jwt),
    api_key: str = Depends(verify_admin_api_key)
):
    recording = db.query(Recording).filter_by(id=recording_id, owner_id=owner_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    verify_md5(file.file, md5_checksum)
    save_fragment_file(owner_id, recording_id, index, recording.file_extension, file)
    new_fragment = Fragment(recording_id=recording_id, index=int(index), sample_number=int(sample_number))
    db.add(new_fragment)
    db.commit()
    db.refresh(new_fragment)
    return new_fragment

@app.put("/{admin_url}/recordings/{recording_id}")
async def admin_update_recording(recording_id: str, recording: RecordingCreate, db: Session = Depends(get_db), user: dict = Depends(verify_admin_jwt), api_key: str = Depends(verify_admin_api_key)):
    """ Updates metadata of a specific recording """
    existing_recording = db.query(Recording).filter_by(id=recording_id).first()
    if not existing_recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    for key, value in recording.model_dump().items():
        setattr(existing_recording, key, value)
    db.commit()
    db.refresh(existing_recording)
    return existing_recording

""" @app.put("/{admin_url}/recordings/{recording_id}/fragments/{index}")
async def admin_update_fragment(recording_id: str, index: int, fragment: FragmentCreate, db: Session = Depends(get_db), user: dict = Depends(verify_admin_jwt), api_key: str = Depends(verify_admin_api_key)):
    #Updates metadata of a specific fragment in a specific recording
    fragment = (
        db.query(Fragment)
        .filter_by(recording_id=recording_id, index=index)
        .first()
    )
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    for key, value in fragment.dict().items():
        setattr(fragment, key, value)
    db.commit()
    db.refresh(fragment)
    return fragment """

@app.delete("/{admin_url}/recordings/{recording_id}")
async def admin_delete_recording(recording_id: str, db: Session = Depends(get_db), user: dict = Depends(verify_admin_jwt), api_key: str = Depends(verify_admin_api_key)):
    """ Deletes a specific recording and associated fragments by recording_id """
    recording = db.query(Recording).filter_by(id=recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    delete_recording_files(recording.owner_id, recording_id)
    db.delete(recording)
    db.commit()
    return {"message": "Recording and associated fragments deleted"}

@app.delete("/{admin_url}/recordings/{recording_id}/fragments/{index}")
async def admin_delete_fragment(recording_id: str, index: int, db: Session = Depends(get_db), user: dict = Depends(verify_admin_jwt), api_key: str = Depends(verify_admin_api_key)):
    """ Deletes a specific fragment in a specific recording by recording_id and fragment index """
    recording = get_admin_recording(db, user, recording_id)
    fragment = (
        db.query(Fragment)
        .filter_by(recording_id=recording_id, index=index)
        .first()
    )
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    delete_fragment_file(recording.owner_id, recording_id, index, recording.file_extension)
    db.delete(fragment)
    db.commit()
    return {"message": "Fragment deleted"}

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=os.getenv('API_HOST', os.getenv("API_HOST")), 
        port=os.getenv('API_PORT', os.getenv("API_PORT"))
    )