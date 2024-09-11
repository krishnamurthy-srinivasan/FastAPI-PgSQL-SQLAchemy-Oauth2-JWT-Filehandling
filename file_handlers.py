from fastapi import FastAPI, HTTPException, Depends, status, APIRouter
from fastapi import UploadFile
from fastapi.responses import FileResponse, StreamingResponse
import json
import yaml
import os
import datetime
import io

BASEPATH = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASEPATH, "converted_files")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

router = APIRouter(prefix="/file", tags=["FileHandler"])

# def flatten_dict():


@router.post("/upload")
async def upload_file(file : UploadFile):
    if file.content_type != "application/json":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported File Type")
    data = file.file.read()
    return {"filename": file.filename, "Content": data}

@router.post("/convert", description="Converts JSON to YAML and returns downloadable file")
async def convert(file: UploadFile):
    if file.content_type != "application/json":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported File Type")
    data = await file.read()
    try:
        data = json.loads(data.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON file")

    yaml_file_name = f"{file.filename.split('.')[0]}_{str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))}.yaml"
    save_path = os.path.join(UPLOAD_DIR, yaml_file_name)
    # os.path.normpath(save_path)
    with open(save_path, "w") as f:
        yaml.dump(data, f, default_flow_style= False)
    return FileResponse(path=save_path, filename=yaml_file_name,media_type="application/octet-stream" )

@router.post("/conver_and_stream", description="Converts JSON to YAML and streams the response as file without saving it locally")
async def convert_and_stream(file: UploadFile):
    if file.content_type != "application/json":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported File Type")
    data = await file.read()
    try:
        data = json.loads(data.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON file")

    yaml_file_name = f"{file.filename.split('.')[0]}_{str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))}.yaml"
    yaml_stream = io.StringIO()

    # Dump the YAML data into the in-memory stream
    yaml.dump(data, yaml_stream, default_flow_style=False, allow_unicode=True)

    # Rewind the stream to the beginning
    yaml_stream.seek(0)

    # Return the in-memory stream as a downloadable file
    response = StreamingResponse(yaml_stream, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={yaml_file_name}"

    return response