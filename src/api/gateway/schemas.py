from pydantic import BaseModel
from fastapi import Form, File, UploadFile
from typing import Optional

class RecordingCreate(BaseModel):
    sample_rate: int
    channel_count: int
    file_extension: str

class FragmentCreate(BaseModel):
    recording_id: str
    index: str = Form(...)
    sample_number: str = Form(...)
    md5_checksum: Optional[str] = Form(None)
#    file: UploadFile = File(...)