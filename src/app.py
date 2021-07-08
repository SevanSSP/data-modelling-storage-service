import json
import time

import click
import uvicorn
from fastapi import FastAPI
from starlette.requests import Request

from config import Config
from services.database import data_source_collection
from storage.internal.data_source_repository import DataSourceRepository
from utils.exceptions import ImportException, InvalidDataSourceException
from utils.logging import logger
from utils.package_import import import_package
from controllers import (
    blob_controller,
    blueprint_controller,
    datasource_controller,
    document_controller,
    explorer_controller,
    package_controller,
    search_controller,
    reference_controller,
)
from utils.wipe_db import wipe_db

server_root = "/api"
version = "v1"
prefix = f"{server_root}/{version}"
app = FastAPI(title="Data Modelling Storage Service", description="API for basic data modelling interaction")
app.include_router(blob_controller.router, prefix=prefix)
app.include_router(datasource_controller.router, prefix=prefix)
app.include_router(document_controller.router, prefix=prefix)
app.include_router(explorer_controller.router, prefix=prefix)
app.include_router(package_controller.router, prefix=prefix)
app.include_router(search_controller.router, prefix=prefix)
app.include_router(blueprint_controller.router, prefix=prefix)
app.include_router(reference_controller.router, prefix=prefix)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    milliseconds = int(round(process_time * 1000))
    logger.debug(f"\t{milliseconds}ms to process request")
    return response


@click.group()
def cli():
    pass


@cli.command()
def run():
    try:
        with open("./version.txt") as version_file:
            print(f"VERSION: {version_file.read()}")
    except FileNotFoundError:
        pass
    uvicorn.run(
        "app:app",
        host="0.0.0.0",  # nosec
        port=5000,
        reload=Config.ENVIRONMENT == "local",
        log_level=Config.LOGGER_LEVEL.lower(),
    )


@cli.command()
def init_application():
    logger.info("IMPORTING CORE DOCUMENTS")
    import_package(f"{Config.APPLICATION_HOME}/system/SIMOS", data_source=Config.CORE_DATA_SOURCE, is_root=True)
    logger.debug("DONE")


@cli.command()
@click.argument("file")
def import_data_source(file):
    try:
        with open(file) as json_file:
            document = json.load(json_file)
            try:
                DataSourceRepository.validate_data_source(document)
            except InvalidDataSourceException as error:
                logger.error(error)
                exit(1)
            id = document["name"]
            document["_id"] = id
            logger.debug(f"Importing {file} as data_source with id: {id}.")
            data_source_collection.replace_one({"_id": id}, document, upsert=True)
    except Exception as error:
        raise ImportException(f"Failed to import file {file}: {error}")


@cli.command()
def nuke_db():
    logger.info("PURGING DATABASE")
    wipe_db()
    logger.debug("DONE")


@cli.command()
@click.pass_context
def reset_app(context):
    context.invoke(nuke_db)
    logger.info("CREATING SYSTEM DATA SOURCE")
    context.invoke(import_data_source, file="/code/home/system/data_sources/system.json")
    logger.debug("DONE")
    context.invoke(init_application)


if __name__ == "__main__":
    cli()
