from typing import Optional

from services.document_service import DocumentService
from restful import response_object as res
from restful.request_types.shared import EntityName
from restful.use_case import UseCase
from storage.internal.data_source_repository import get_data_source


class RenameRequest(EntityName):
    parentId: Optional[str] = None
    documentId: str
    data_source_id: Optional[str] = None


class RenameUseCase(UseCase):
    def __init__(self, repository_provider=get_data_source):
        self.repository_provider = repository_provider

    def process_request(self, req: RenameRequest):

        document_service = DocumentService(repository_provider=self.repository_provider)
        document = document_service.rename_document(
            data_source_id=req.data_source_id, document_id=req.documentId, parent_uid=req.parentId, name=req.name,
        )
        document_service.invalidate_cache()
        return res.ResponseSuccess(document)