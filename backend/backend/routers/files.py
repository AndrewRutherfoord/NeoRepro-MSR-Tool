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

router = APIRouter()

QUERIES_PATH = "queries"
CONFIGS_PATH = "configs"
DB_EXPORTS_PATH = "../neo4j_import"


def get_file_list(path):
    files_structure = {}

    for root, dirs, files in os.walk(path):
        path = root.split(os.sep)
        subdir = files_structure
        for sub in path[1:]:
            subdir = subdir.setdefault(sub, {})
        subdir.update({file: None for file in files})

    return files_structure


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


def delete_file(path, file_name):
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


# ----- Query Files -----


@router.get("/queries/", response_model=dict)
async def list_files():
    return get_file_list(QUERIES_PATH)


class SaveBody(BaseModel):
    content: str


@router.post("/queries/{path:path}")
async def save_query_file(path: str, body: SaveBody):
    try:
        save_file(QUERIES_PATH, path, body.content)
        return Response(status_code=201)
    except FileExistsError as e:
        raise HTTPException(400, "File already exists.")


@router.get("/queries/{path:path}")
async def get_query_file(path: str):
    file_path = os.path.join(QUERIES_PATH, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@router.delete("/queries/{path:path}")
async def delete_query_file(path: str):
    try:
        delete_file(QUERIES_PATH, path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


# ----- Config Files -----


@router.get("/configs/", response_model=dict)
async def list_files():
    return get_file_list(CONFIGS_PATH)


@router.post("/configs/{path:path}")
async def save_query_file(path: str, body: SaveBody):
    print(f"Saving config file {path}")
    try:
        created = save_file(CONFIGS_PATH, path, body.content)
        return Response(status_code=201 if created else 200)
    except FileExistsError as e:
        raise HTTPException(400, "File already exists.")


@router.get("/configs/{path:path}")
async def get_query_file(path: str):
    file_path = os.path.join(CONFIGS_PATH, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@router.delete("/configs/{path:path}")
async def delete_query_file(path: str):
    try:
        delete_file(CONFIGS_PATH, path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    
# ----- DB Export Files -----

@router.get("/db-exports/", response_model=dict)
async def list_files():
    return get_file_list(DB_EXPORTS_PATH)

