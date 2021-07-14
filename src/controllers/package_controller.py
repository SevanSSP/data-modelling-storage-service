from fastapi import APIRouter
from starlette.responses import JSONResponse

from domain_classes.dto import DTO
from services.document_service import DocumentService
from storage.internal.data_source_repository import get_data_source
from utils.exceptions import FileNotFoundException

router = APIRouter()


@router.get("/packages/{data_source_id}", operation_id="package_get")
def get(data_source_id: str):
    """
    List all root packages in the requested data source
    """
    # TODO: Use UseCase. If not, it will return 500 on a 404
    document_service = DocumentService(repository_provider=get_data_source)
    root_packages = document_service.get_root_packages(data_source_id=data_source_id)
    return JSONResponse([package.to_dict() for package in root_packages])


@router.get("/packages/{data_source_id}/findByName/{name}", operation_id="package_find_by_name")
def find_by_name(data_source_id: str, name: str):
    """
    Get a root package by it's exact name
    """
    package: DTO = get_data_source(data_source_id).first(
        {"type": "system/SIMOS/Package", "isRoot": True, "name": name}
    )
    if not package:
        raise FileNotFoundException(data_source_id, name)
    return JSONResponse(package.to_dict()["data"])
