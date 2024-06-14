import json
import os

from fastapi import (
    APIRouter,
    HTTPException,
    Response,
)

import logging

from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

PATH = "queries"

@router.get("/", response_model=dict)
async def list_files():
    files_structure = {}
    
    for root, dirs, files in os.walk(PATH):
        path = root.split(os.sep)
        subdir = files_structure
        for sub in path[1:]:
            subdir = subdir.setdefault(sub, {})
        subdir.update({file: None for file in files})
    
    return files_structure

class SaveBody(BaseModel):
    content: str

@router.post('/save/{path:path}')
async def save_query_file(path : str, body: SaveBody):
    file_path = os.path.join(PATH, path)
    directory = os.path.dirname(file_path)

    # Create directories if they don't exist
    os.makedirs(directory, exist_ok=True)
    
    logger.warning(body)
    if os.path.isfile(file_path):
        return {"errror": "ERR"}
        # return HTTPException(status_code=400, detail={"message": f"File '{path}' already exists."})
    else:
        with open(file_path, 'w') as file:
            file.write(body.content)
        return Response(status_code=201)
            
    
@router.get("/{path:path}")
async def get_query_file(path: str):
    file_path = os.path.join(PATH, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        return HTTPException(status_code=404, detail="File not found")

@router.delete("/{path:path}")
async def delete_query_file(path: str):
    file_path = os.path.join(PATH, path)
    if os.path.isfile(file_path):
        os.remove(file_path)

        # Remove any empty directories
        directory = os.path.dirname(file_path)
        while directory != PATH:
            if not os.listdir(directory):
                os.rmdir(directory)
                directory = os.path.dirname(directory)
            else:
                break
        
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")