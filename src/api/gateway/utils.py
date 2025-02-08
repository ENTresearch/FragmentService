from typing import Union
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from gateway.models import Recording, Fragment
import jwt
import datetime
import os 
import base64

def generate_api_secret() -> str:
    return base64.urlsafe_b64encode(os.urandom(64)).decode('utf-8')

def generate_api_key(role, ref, iss = "fileserver", expiry_days = 365*10) -> str:
    iat = datetime.datetime.now(datetime.timezone.utc)
    exp = iat + datetime.timedelta(days=expiry_days)
    
    payload = {
        'iss': iss,
        'role': role,
        'ref': ref,
        'iat': int(iat.timestamp()),
        'exp': int(exp.timestamp())
    }
    
    secret = os.getenv("API_KEY_SECRET")
    token = jwt.encode(payload, secret, algorithm='HS256')

    return token

def get_fragment_in_recording(db: Session, recording_id: str, index: int, user_id: str) -> Union[Fragment, Recording]:
    """ Requires recording_id and fragment index and returns corresponding fragment metadata and recording metadata extracted from the database. It does not check the user_id permissions, """
    recording = (
        db.query(Recording)
        .filter_by(id=recording_id, owner_id=user_id)
        .options(joinedload(Recording.fragments))
        .first()
    )
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    if str(recording.owner_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    fragment = next((f for f in recording.fragments if f.index == index), None)

    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    return fragment, recording
