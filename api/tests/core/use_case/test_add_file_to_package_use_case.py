from unittest import mock
from uuid import uuid4

from core.domain.document import Document
from core.use_case.add_file_to_package_use_case import AddFileToPackageRequestObject, AddFileToPackageUseCase
from core.repository.interface.document_repository import DocumentRepository


def test_without_parameters():

    document_repository: DocumentRepository = mock.Mock()

    parent_id = str(uuid4())

    parent = Document(uid=parent_id, path="/", filename="root", type="folder", template_ref="")

    def mock_add(document):
        pass

    document_repository.add.return_value = mock_add
    document_repository.get.return_value = parent

    use_case = AddFileToPackageUseCase(document_repository=document_repository)
    data = {"parentId": parent_id, "filename": "new_file", "templateRef": ""}
    request_object = AddFileToPackageRequestObject.from_dict(data)
    response_object = use_case.execute(request_object)

    assert bool(response_object) is True
    document_repository.get.assert_called_with(parent_id)

    result = response_object.value.to_dict()

    assert result["filename"] == data["filename"]