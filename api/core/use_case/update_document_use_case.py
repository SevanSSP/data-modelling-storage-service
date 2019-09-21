from core.domain.document import Document
from core.repository.interface.document_repository import DocumentRepository


class UpdateDocumentUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    def execute(self, document_id: str, form_data: dict) -> Document:
        document: Document = self.document_repository.get(document_id)
        document.form_data = form_data
        self.document_repository.update(document)
        return document
