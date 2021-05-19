import unittest
from unittest import mock, skip

from pydantic import ValidationError

from domain_classes.dto import DTO
from restful.request_types.shared import Reference
from services.document_service import DocumentService
from tests.unit.mock_blueprint_provider import blueprint_provider
from utils.exceptions import EntityNotFoundException, InvalidEntityException


class ReferenceTestCase(unittest.TestCase):
    def test_insert_reference(self):
        repository = mock.Mock()

        doc_storage = {
            "1": {
                "_id": "1",
                "name": "Parent",
                "description": "",
                "type": "uncontained_blueprint",
                "uncontained_in_every_way": {},
            },
            "2d7c3249-985d-43d2-83cf-a887e440825a": {
                "_id": "2d7c3249-985d-43d2-83cf-a887e440825a",
                "name": "something",
                "description": "",
                "type": "blueprint_2",
            },
        }

        def mock_update(dto: DTO, storage_attribute):
            doc_storage[dto.uid] = dto.data
            return None

        repository.get = lambda x: DTO(doc_storage[str(x)])
        repository.update = mock_update
        document_service = DocumentService(
            blueprint_provider=blueprint_provider, repository_provider=lambda x: repository
        )

        document_service.insert_reference(
            "testing",
            document_id="1",
            reference=Reference.parse_obj(
                {"_id": "2d7c3249-985d-43d2-83cf-a887e440825a", "name": "something", "type": "blueprint_2"}
            ),
            attribute_path="uncontained_in_every_way",
        )
        assert doc_storage["1"]["uncontained_in_every_way"] == {
            "_id": "2d7c3249-985d-43d2-83cf-a887e440825a",
            "name": "something",
            "type": "blueprint_2",
        }

    def test_insert_reference_target_does_not_exist(self):
        repository = mock.Mock()

        doc_storage = {
            "1": {
                "_id": "1",
                "name": "Parent",
                "description": "",
                "type": "uncontained_blueprint",
                "uncontained_in_every_way": {},
            }
        }

        def mock_get(document_id: str):
            try:
                return DTO(doc_storage[str(document_id)])
            except KeyError:
                raise EntityNotFoundException(f"{document_id} was not found in the 'test' data-sources lookupTable")

        def mock_update(dto: DTO, storage_attribute):
            doc_storage[dto.uid] = dto.data
            return None

        repository.get = mock_get
        repository.update = mock_update
        document_service = DocumentService(
            blueprint_provider=blueprint_provider, repository_provider=lambda x: repository
        )

        with self.assertRaises(EntityNotFoundException):
            document_service.insert_reference(
                "testing",
                document_id="1",
                reference=Reference.parse_obj(
                    {"_id": "2d7c3249-985d-43d2-83cf-a887e440825a", "name": "something", "type": "something"}
                ),
                attribute_path="uncontained_in_every_way",
            )

    def test_insert_reference_target_exists_but_wrong_type(self):
        repository = mock.Mock()

        doc_storage = {
            "1": {
                "_id": "1",
                "name": "Parent",
                "description": "",
                "type": "uncontained_blueprint",
                "uncontained_in_every_way": {},
            },
            "2d7c3249-985d-43d2-83cf-a887e440825a": {
                "_id": "2d7c3249-985d-43d2-83cf-a887e440825a",
                "name": "something",
                "description": "hgallo",
                "type": "ExtendedBlueprint",
                "another_value": "hei du",
            },
        }

        def mock_update(dto: DTO, storage_attribute):
            doc_storage[dto.uid] = dto.data

        repository.get = lambda x: DTO(doc_storage[str(x)])
        repository.update = mock_update
        document_service = DocumentService(
            blueprint_provider=blueprint_provider, repository_provider=lambda x: repository
        )

        with self.assertRaises(InvalidEntityException):
            document_service.insert_reference(
                "testing",
                document_id="1",
                reference=Reference.parse_obj(
                    {"_id": "2d7c3249-985d-43d2-83cf-a887e440825a", "name": "something", "type": "wrong_type"}
                ),
                attribute_path="uncontained_in_every_way",
            )

    def test_insert_reference_too_many_attributes(self):
        repository = mock.Mock()

        doc_storage = {
            "1": {
                "_id": "1",
                "name": "Parent",
                "description": "",
                "type": "uncontained_blueprint",
                "uncontained_in_every_way": {},
            },
            "2d7c3249-985d-43d2-83cf-a887e440825a": {
                "_id": "2d7c3249-985d-43d2-83cf-a887e440825a",
                "name": "something",
                "description": "",
                "type": "blueprint_2",
            },
        }

        def mock_get(document_id: str):
            return DTO(doc_storage[str(document_id)])

        def mock_update(dto: DTO, storage_attribute):
            doc_storage[dto.uid] = dto.data
            return None

        repository.get = mock_get
        repository.update = mock_update
        document_service = DocumentService(
            blueprint_provider=blueprint_provider, repository_provider=lambda x: repository
        )

        document_service.insert_reference(
            "testing",
            document_id="1",
            reference=Reference.parse_obj(
                {
                    "_id": "2d7c3249-985d-43d2-83cf-a887e440825a",
                    "name": "something",
                    "type": "blueprint_2",
                    "description": "hallO",
                    "something": "something",
                }
            ),
            attribute_path="uncontained_in_every_way",
        )
        assert doc_storage["1"]["uncontained_in_every_way"] == {
            "_id": "2d7c3249-985d-43d2-83cf-a887e440825a",
            "name": "something",
            "type": "blueprint_2",
        }

    def test_insert_reference_missing_required_attribute(self):
        repository = mock.Mock()

        doc_storage = {
            "1": {
                "_id": "1",
                "name": "Parent",
                "description": "",
                "type": "uncontained_blueprint",
                "uncontained_in_every_way": {},
            }
        }

        def mock_get(document_id: str):
            return DTO(doc_storage[document_id])

        def mock_update(dto: DTO, storage_attribute):
            doc_storage[dto.uid] = dto.data
            return None

        repository.get = mock_get
        repository.update = mock_update
        document_service = DocumentService(
            blueprint_provider=blueprint_provider, repository_provider=lambda x: repository
        )

        with self.assertRaises(ValidationError):
            document_service.insert_reference(
                "testing",
                document_id="1",
                reference=Reference.parse_obj({"_id": "something", "type": "something"}),
                attribute_path="uncontained_in_every_way",
            )

    def test_remove_reference(self):
        repository = mock.Mock()

        doc_storage = {
            "1": {
                "_id": "1",
                "name": "Parent",
                "description": "",
                "type": "uncontained_blueprint",
                "uncontained_in_every_way": {
                    "_id": "something",
                    "name": "something",
                    "description": "",
                    "type": "blueprint_2",
                },
            },
            "something": {"_id": "something", "name": "something", "description": "", "type": "blueprint_2",},
        }

        def mock_update(dto: DTO, storage_attribute):
            doc_storage[dto.uid] = dto.data
            return None

        repository.get = lambda id: DTO(doc_storage[id])
        repository.update = mock_update
        document_service = DocumentService(
            blueprint_provider=blueprint_provider, repository_provider=lambda x: repository
        )

        document_service.remove_reference(
            "testing", document_id="1", attribute_path="uncontained_in_every_way",
        )
        assert doc_storage["1"]["uncontained_in_every_way"] == {}

    def test_remove_nested_reference(self):
        repository = mock.Mock()

        doc_storage = {
            "1": {
                "_id": "1",
                "name": "Parent",
                "description": "",
                "type": "blueprint_with_second_level_nested_uncontained_attribute",
                "i_have_a_uncontained_attribute": {
                    "name": "something",
                    "description": "",
                    "type": "uncontained_blueprint",
                    "uncontained_in_every_way": {
                        "_id": "something",
                        "name": "something",
                        "description": "",
                        "type": "blueprint_2",
                    },
                },
            },
            "something": {"_id": "something", "name": "something", "description": "", "type": "blueprint_2",},
        }

        def mock_update(dto: DTO, storage_attribute):
            doc_storage[dto.uid] = dto.data
            return None

        repository.get = lambda id: DTO(doc_storage[id])
        repository.update = mock_update
        document_service = DocumentService(
            blueprint_provider=blueprint_provider, repository_provider=lambda x: repository
        )

        document_service.remove_reference(
            "testing", document_id="1", attribute_path="i_have_a_uncontained_attribute.uncontained_in_every_way",
        )
        assert doc_storage["1"]["i_have_a_uncontained_attribute"]["uncontained_in_every_way"] == {}

    @skip
    def test_remove_reference_in_list(self):
        raise NotImplementedError(
            "Removing references where the attribute " "path contains list indexes probably does not work"
        )
