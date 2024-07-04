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
logger.addHandler(logging.StreamHandler())

# This file contains the endpoints for managing saved query and config file.
# Also has list method for Neo4j import
router = APIRouter()

QUERIES_PATH = "queries"
CONFIGS_PATH = "configs"
DB_EXPORTS_PATH = "../neo4j_import"


BASE_PATHS = {
    "queries": QUERIES_PATH,
    "configs": CONFIGS_PATH,
    "db-exports": DB_EXPORTS_PATH,
}


class SaveBody(BaseModel):
    content: str


# ---------- File Management Methods ----------
def get_file_type(file_type: str):
    try:
        return BASE_PATHS[file_type]
    except KeyError as e:
        raise HTTPException(404, "File type is invalid.")


def get_file_list(path):
    """Returns a list of files from the base path"""
    files_structure = {}

    for root, dirs, files in os.walk(path):
        path = root.split(os.sep)
        subdir = files_structure
        for sub in path[1:]:
            subdir = subdir.setdefault(sub, {})
        subdir.update({file: None for file in files})

    return files_structure


@router.get("/files/{file_type:str}/", response_model=dict)
async def list_files(file_type: str):
    base_path = get_file_type(file_type)
    return get_file_list(base_path)


@router.get("/files/{file_type:str}/{path:path}", response_model=dict)
async def get_file(file_type: str, path: str):
    base_path = get_file_type(file_type)
    file_path = os.path.join(base_path, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")


def save_file(path, file_name, content):
    """Saves a file to the specified path.

    Args:
        path (str): Base path to save the file.
        file_name (str): Name of the file to save. Can include directory structure.
        content (str): Content to save to file.

    Returns:
        Boolean: True if file was created, False if file already existed.
    """
    file_path = os.path.join(path, file_name)
    directory = os.path.dirname(file_path)

    # Create directories if they don't exist
    os.makedirs(directory, exist_ok=True)

    if os.path.isfile(file_path):
        logger.info(f"File {file_path} already exists. Overwriting.")
        created = False
    else:
        logger.info(f"File {file_path} does not exist. Creating.")
        created = True

    with open(file_path, "w") as file:
        file.write(content)
    return created


@router.post("/files/{file_type:str}/{path:path}")
async def save_file(file_type: str, path: str, body: SaveBody):
    try:
        base_path = get_file_type()
        save_file(base_path, path, body.content)
        return Response(status_code=201)
    except FileExistsError as e:
        raise HTTPException(400, "File already exists.")


def delete_file(path, file_name):
    """Deletes a given file and then deletes any directories it was in that are empty"""
    file_path = os.path.join(path, file_name)
    if os.path.isfile(file_path):
        os.remove(file_path)

        # Remove any empty directories
        directory = os.path.dirname(file_path)
        while directory != path:
            if not os.listdir(directory):
                os.rmdir(directory)
                directory = os.path.dirname(directory)
            else:
                break
    else:
        raise FileNotFoundError()


@router.delete("/files/{file_type:str}/{path:path}")
async def delete_file(file_type: str, path: str):
    try:
        delete_file(CONFIGS_PATH, path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
