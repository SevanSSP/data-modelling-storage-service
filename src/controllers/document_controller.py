from typing import Optional

from fastapi import APIRouter
from pydantic import conint
from starlette.responses import JSONResponse

from use_case.get_document_by_path_use_case import GetDocumentByPathRequest, GetDocumentByPathUseCase
from use_case.get_document_use_case import GetDocumentRequest, GetDocumentUseCase
from use_case.update_document_use_case import UpdateDocumentRequest, UpdateDocumentUseCase
from restful.status_codes import STATUS_CODES

from use_case.get_document_use_case import GetDocumentResponse

from use_case.get_document_by_path_use_case import GetDocumentByPathResponse

router = APIRouter()


@router.get(
    "/documents/{data_source_id}/{document_id}", operation_id="document_get_by_id", response_model=GetDocumentResponse
)
def get_by_id(
    data_source_id: str,
    document_id: str,
    ui_recipe: Optional[str] = None,
    attribute: Optional[str] = None,
    depth: conint(gt=-1, lt=1000) = 999,
):
    use_case = GetDocumentUseCase()
    response: GetDocumentResponse = use_case.execute(
        GetDocumentRequest(
            data_source_id=data_source_id,
            document_id=document_id,
            ui_recipe=ui_recipe,
            attribute=attribute,
            depth=depth,
        )
    )
    return JSONResponse(response.value, status_code=STATUS_CODES[response.type])


@router.get(
    "/documents-by-path/{data_source_id}",
    operation_id="document_get_by_path",
    response_model=GetDocumentByPathResponse,
)
def get_by_path(
    data_source_id: str, ui_recipe: Optional[str] = None, attribute: Optional[str] = None, path: Optional[str] = None
):
    """
    Get a document by it's path in the form "{dataSource}/{rootPackage}/{subPackage(s)?/{name}
    """
    use_case = GetDocumentByPathUseCase()
    response: GetDocumentByPathResponse = use_case.execute(
        GetDocumentByPathRequest(data_source_id=data_source_id, path=path, ui_recipe=ui_recipe, attribute=attribute)
    )
    return JSONResponse(response.value, status_code=STATUS_CODES[response.type])


@router.put("/documents/{data_source_id}/{document_id}", operation_id="document_update")
def update(data_source_id: str, document_id: str, data: dict, attribute: Optional[str] = None):
    update_use_case = UpdateDocumentUseCase()
    response = update_use_case.execute(
        UpdateDocumentRequest(data_source_id=data_source_id, data=data, document_id=document_id, attribute=attribute)
    )
    return JSONResponse(response.value, status_code=STATUS_CODES[response.type])