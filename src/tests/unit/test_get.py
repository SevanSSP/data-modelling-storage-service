import unittest
from unittest import mock

from domain_classes.dto import DTO
from services.document_service import DocumentService
from tests.unit.mock_blueprint_provider import blueprint_provider
from utils.data_structure.compare import pretty_eq


class DocumentServiceTestCase(unittest.TestCase):
    def test_get_complete_document(self):
        document_1 = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "blueprint_1",
            "nested": {"name": "Nested", "description": "", "type": "blueprint_2"},
            "reference": {"_id": "2", "name": "Reference", "type": "blueprint_2"},
            "references": [
                {"_id": "3", "name": "Reference1", "type": "blueprint_2"},
                {"_id": "4", "name": "Reference2", "type": "blueprint_2"},
            ],
        }

        document_2 = {"_id": "2", "name": "Reference", "description": "", "type": "blueprint_2"}
        document_3 = {"_id": "3", "name": "Reference1", "description": "", "type": "blueprint_2"}
        document_4 = {"_id": "4", "name": "Reference2", "description": "", "type": "blueprint_2"}

        def mock_get(document_id: str):
            if document_id == "1":
                return DTO(data=document_1.copy())
            if document_id == "2":
                return DTO(data=document_2.copy())
            if document_id == "3":
                return DTO(data=document_3.copy())
            if document_id == "4":
                return DTO(data=document_4.copy())
            return None

        document_repository = mock.Mock()
        document_repository.get = mock_get

        document_service: DocumentService = DocumentService(
            repository_provider=lambda x, y: document_repository, blueprint_provider=blueprint_provider
        )
        root = document_service.get_node_by_uid("datasource", "1").to_dict()

        assert isinstance(root, dict)

        actual = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "blueprint_1",
            "nested": {"name": "Nested", "description": "", "type": "blueprint_2"},
            "reference": document_2,
            "references": [document_3, document_4],
        }

        assert pretty_eq(actual, root) is None

    def test_get_complete_nested_reference(self):
        document_1 = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "blueprint_with_second_level_reference",
            "contained_with_child_references": {
                "name": "First child",
                "description": "",
                "type": "blueprint_1",
                "nested": {"name": "Nested", "description": "", "type": "blueprint_2"},
                "reference": {"_id": "2", "name": "Reference", "type": "blueprint_2"},
                "references": [
                    {"_id": "3", "name": "Reference1", "type": "blueprint_2"},
                    {"_id": "4", "name": "Reference2", "type": "blueprint_2"},
                ],
            },
        }

        document_2 = {"_id": "2", "name": "Reference", "description": "", "type": "blueprint_2"}
        document_3 = {"_id": "3", "name": "Reference1", "description": "", "type": "blueprint_2"}
        document_4 = {"_id": "4", "name": "Reference2", "description": "", "type": "blueprint_2"}

        def mock_get(document_id: str):
            if document_id == "1":
                return DTO(data=document_1.copy())
            if document_id == "2":
                return DTO(data=document_2.copy())
            if document_id == "3":
                return DTO(data=document_3.copy())
            if document_id == "4":
                return DTO(data=document_4.copy())
            return None

        document_repository = mock.Mock()
        document_repository.get = mock_get

        document_service: DocumentService = DocumentService(
            repository_provider=lambda x, y: document_repository, blueprint_provider=blueprint_provider
        )
        root = document_service.get_node_by_uid("datasource", "1").to_dict()

        assert isinstance(root, dict)

        actual = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "blueprint_with_second_level_reference",
            "contained_with_child_references": {
                "name": "First child",
                "description": "",
                "type": "blueprint_1",
                "nested": {"name": "Nested", "description": "", "type": "blueprint_2"},
                "reference": document_2,
                "references": [document_3, document_4],
            },
        }

        assert pretty_eq(actual, root) is None
