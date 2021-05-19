from fastapi import APIRouter

from restful.request_types.shared import Reference
from use_case.delete_reference_use_case import DeleteReferenceRequest, DeleteReferenceUseCase
from use_case.insert_reference_use_case import InsertReferenceRequest, InsertReferenceUseCase

router = APIRouter()


@router.put("/reference/{data_source_id}/{document_dotted_id}", operation_id="reference_insert", response_model=dict)
def insert_reference(data_source_id: str, document_dotted_id: str, reference: Reference):
    use_case = InsertReferenceUseCase()
    document_id, attribute = document_dotted_id.split(".", 1)
    response = use_case.execute(
        InsertReferenceRequest(
            data_source_id=data_source_id, document_id=document_id, reference=reference, attribute=attribute
        )
    )
    return response.value


@router.delete(
    "/reference/{data_source_id}/{document_dotted_id}", operation_id="reference_delete", response_model=dict
)
def delete_reference(data_source_id: str, document_dotted_id: str):
    use_case = DeleteReferenceUseCase()
    document_id, attribute = document_dotted_id.split(".", 1)
    response = use_case.execute(
        DeleteReferenceRequest(data_source_id=data_source_id, document_id=document_id, attribute=attribute)
    )
    return response.value
