import unittest
from unittest import mock

import pytest

from common.tree_node_serializer import tree_node_to_dict
from common.utils.data_structure.compare import pretty_eq
from common.utils.data_structure.is_same import is_same
from enums import REFERENCE_TYPES, SIMOS, Protocols
from tests.unit.mock_utils import get_mock_document_service


class DocumentServiceTestCase(unittest.TestCase):
    def test_references_that_uses_wrong_protocol(self):
        my_car_rental = {
            "_id": "1",
            "type": "test_data/complex/CarRental",
            "name": "myCarRental",
            "description": "",
            "extends": [SIMOS.NAMED_ENTITY.value],
            "cars": [
                {"type": "test_data/complex/CarTest", "name": "Volvo 240", "plateNumber": "123"},
                {"type": "test_data/complex/CarTest", "name": "Ferrari", "plateNumber": "456"},
            ],
            "customers": [
                {
                    "type": "test_data/complex/Customer",
                    "name": "Wrong protocol",
                    "car": {
                        "address": "wrong:///$1.cars.0",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                }
            ],
        }

        def mock_get(document_id: str):
            if document_id == "1":
                return my_car_rental.copy()
            return None

        def mock_find(target: dict):
            # Used when resolving reference using paths.
            return [
                {
                    "content": [
                        {"address": "$1", "type": SIMOS.REFERENCE.value, "referenceType": REFERENCE_TYPES.LINK.value},
                    ]
                }
            ]

        document_repository = mock.Mock()
        document_repository.get = mock_get
        document_repository.find = mock_find

        document_service = get_mock_document_service(lambda x, y: document_repository)
        with pytest.raises(Exception, match=r"The protocol 'wrong' is not supported"):
            tree_node_to_dict(document_service.get_document("datasource/$1", resolve_links=True, depth=9))

    def test_references(self):
        my_car_rental = {
            "_id": "2",
            "type": "test_data/complex/CarRental",
            "name": "myCarRental",
            "description": "",
            "extends": [SIMOS.NAMED_ENTITY.value],
            "cars": [
                {
                    "type": "test_data/complex/CarTest",
                    "name": "Volvo 240",
                    "plateNumber": "123",
                    "engine": {
                        "address": f"{Protocols.DMSS.value}://another_data_source/$3",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
                {
                    "type": "test_data/complex/CarTest",
                    "name": "Ferrari",
                    "plateNumber": "456",
                    "engine": {
                        "address": f"{Protocols.DMSS.value}://another_data_source/parts/engines/myEngine",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
            ],
            "customers": [
                {
                    "type": "test_data/complex/Customer",
                    "name": "Full absolute path prefixed with protocol",
                    "car": {
                        "address": f"{Protocols.DMSS.value}://test_data/complex/myCarRental.cars[0]",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the destination data source by id",
                    "car": {
                        "address": f"/$2.cars[0]",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the destination data source by path",
                    "car": {
                        "address": f"/complex/myCarRental.cars[0]",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the destination data source by query",
                    "car": {
                        "address": f"/[(_id=1)].content[(name=myCarRental)].cars[0]",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the destination data source by query on array",
                    "car": {
                        "address": f"/[(_id=1)].content[(name=myCarRental)].cars[(name=Volvo 240)]",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Test",
                    "car": {
                        "address": f"/complex.content[(name=myCarRental)].cars[0]",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Test2",
                    "car": {
                        "address": f"/complex.content[0].cars[0]",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the document",
                    "car": {
                        "address": f"^.cars[0]",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the document with query on plate number",
                    "car": {
                        "address": f"^.cars[(plateNumber=456,name=Ferrari)]",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": REFERENCE_TYPES.LINK.value,
                    },
                },
            ],
        }

        test_data_data_source = [
            {
                "_id": "1",
                "name": "complex",
                "isRoot": True,
                "type": SIMOS.PACKAGE.value,
                "content": [
                    {"address": "$2", "type": SIMOS.REFERENCE.value, "referenceType": REFERENCE_TYPES.LINK.value},
                ],
            }
        ]

        def mock_get_inside_test_data(document_id: str):
            if document_id == "1":
                return test_data_data_source[0].copy()
            if document_id == "2":
                return my_car_rental.copy()
            return None

        my_engine = {
            "_id": "3",
            "name": "myEngine",
            "description": "Some description",
            "fuelPump": {
                "name": "fuelPump",
                "description": "A standard fuel pump",
                "type": "test_data/complex/FuelPumpTest",
            },
            "power": 120,
            "type": "test_data/complex/EngineTest",
        }

        engines = {
            "_id": "2",
            "name": "engines",
            "isRoot": True,
            "content": [
                {"address": "$3", "type": SIMOS.REFERENCE.value, "referenceType": REFERENCE_TYPES.LINK.value},
            ],
        }

        another_data_source = [
            {
                "_id": "1",
                "name": "parts",
                "isRoot": True,
                "content": [
                    {"address": "$2", "type": SIMOS.REFERENCE.value, "referenceType": REFERENCE_TYPES.LINK.value},
                ],
            },
            my_engine,
        ]

        def mock_get_inside_another_data_source(document_id: str):
            if document_id == "1":
                return another_data_source[0].copy()
            if document_id == "2":
                return engines.copy()
            if document_id == "3":
                return my_engine.copy()
            return None

        def find(target: dict, data_source: list) -> dict:
            """Utility method to be able to search for a document inside a test data source."""
            hit = next((f for f in data_source if is_same(f, target)), None)
            if hit:
                return [hit.copy()]

        def mock_data_source(data_source_id: str, user: dict):
            document_repository = mock.Mock()
            document_repository.name = data_source_id
            if data_source_id == "test_data":
                document_repository.get = mock_get_inside_test_data
                document_repository.find = lambda target: find(target, test_data_data_source)
            if data_source_id == "another_data_source":
                document_repository.get = mock_get_inside_another_data_source
                document_repository.find = lambda target: find(target, another_data_source)
            return document_repository

        document_service = get_mock_document_service(mock_data_source)
        directly = tree_node_to_dict(document_service.get_document("test_data/$2", resolve_links=True, depth=99))
        complex_package = tree_node_to_dict(
            document_service.get_document("test_data/$1", resolve_links=True, depth=99)
        )

        assert isinstance(directly, dict)

        actual = {
            "_id": "2",
            "type": "test_data/complex/CarRental",
            "name": "myCarRental",
            "cars": [{"type": "test_data/complex/CarTest", "name": "Volvo 240"}],
            "customers": [
                {
                    "type": "test_data/complex/Customer",
                    "name": "Full absolute path prefixed with protocol",
                    "car": {"type": "test_data/complex/CarTest", "name": "Volvo 240"},
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the destination data source by id",
                    "car": {"type": "test_data/complex/CarTest", "name": "Volvo 240"},
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the destination data source by path",
                    "car": {"type": "test_data/complex/CarTest", "name": "Volvo 240"},
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the destination data source by query",
                    "car": {"type": "test_data/complex/CarTest", "name": "Volvo 240"},
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the destination data source by query on array",
                    "car": {"type": "test_data/complex/CarTest", "name": "Volvo 240"},
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Test",
                    "car": {"type": "test_data/complex/CarTest", "name": "Volvo 240"},
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Test2",
                    "car": {"type": "test_data/complex/CarTest", "name": "Volvo 240"},
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the document",
                    "car": {"type": "test_data/complex/CarTest", "name": "Volvo 240"},
                },
                {
                    "type": "test_data/complex/Customer",
                    "name": "Relative from the document with query on plate number",
                    "car": {"type": "test_data/complex/CarTest", "name": "Ferrari"},
                },
            ],
        }

        assert pretty_eq(actual, directly) is None
        assert pretty_eq(actual, complex_package["content"][0]) is None

    def test_get_complete_document(self):
        document_1 = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {"name": "Nested", "description": "", "type": "basic_blueprint"},
            "reference": {"address": "$2", "type": SIMOS.REFERENCE.value, "referenceType": REFERENCE_TYPES.LINK.value},
            "references": [
                {"address": "$3", "type": SIMOS.REFERENCE.value, "referenceType": REFERENCE_TYPES.LINK.value},
                {"address": "$4", "type": SIMOS.REFERENCE.value, "referenceType": REFERENCE_TYPES.LINK.value},
            ],
        }

        document_2 = {"_id": "2", "name": "Reference", "description": "", "type": "basic_blueprint"}
        document_3 = {"_id": "3", "name": "Reference1", "description": "", "type": "basic_blueprint"}
        document_4 = {"_id": "4", "name": "Reference2", "description": "", "type": "basic_blueprint"}

        def mock_get(document_id: str):
            if document_id == "1":
                return document_1.copy()
            if document_id == "2":
                return document_2.copy()
            if document_id == "3":
                return document_3.copy()
            if document_id == "4":
                return document_4.copy()
            return None

        document_repository = mock.Mock()
        document_repository.get = mock_get

        document_service = get_mock_document_service(lambda x, y: document_repository)
        root = tree_node_to_dict(document_service.get_document("datasource/$1", 99, resolve_links=True))

        assert isinstance(root, dict)

        actual = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {"name": "Nested", "description": "", "type": "basic_blueprint"},
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
                "type": "all_contained_cases_blueprint",
                "nested": {"name": "Nested", "description": "", "type": "basic_blueprint"},
                "reference": {
                    "address": "$2",
                    "type": SIMOS.REFERENCE.value,
                    "referenceType": REFERENCE_TYPES.LINK.value,
                },
                "references": [
                    {"address": "$3", "type": SIMOS.REFERENCE.value, "referenceType": REFERENCE_TYPES.LINK.value},
                    {"address": "$4", "type": SIMOS.REFERENCE.value, "referenceType": REFERENCE_TYPES.LINK.value},
                ],
            },
        }

        document_2 = {"_id": "2", "name": "Reference", "description": "", "type": "basic_blueprint"}
        document_3 = {"_id": "3", "name": "Reference1", "description": "", "type": "basic_blueprint"}
        document_4 = {"_id": "4", "name": "Reference2", "description": "", "type": "basic_blueprint"}

        def mock_get(document_id: str):
            if document_id == "1":
                return document_1.copy()
            if document_id == "2":
                return document_2.copy()
            if document_id == "3":
                return document_3.copy()
            if document_id == "4":
                return document_4.copy()
            return None

        document_repository = mock.Mock()
        document_repository.get = mock_get

        document_service = get_mock_document_service(lambda x, y: document_repository)
        doc = document_service.get_document("datasource/$1", resolve_links=True, depth=99)
        root = tree_node_to_dict(doc)

        assert isinstance(root, dict)

        actual = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "blueprint_with_second_level_reference",
            "contained_with_child_references": {
                "name": "First child",
                "description": "",
                "type": "all_contained_cases_blueprint",
                "nested": {"name": "Nested", "description": "", "type": "basic_blueprint"},
                "reference": document_2,
                "references": [document_3, document_4],
            },
        }

        assert pretty_eq(actual, root) is None
