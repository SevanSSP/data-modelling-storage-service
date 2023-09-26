import unittest

from common.tree_node_serializer import tree_node_from_dict, tree_node_to_dict
from common.utils.data_structure.compare import get_and_print_diff
from domain_classes.blueprint_attribute import BlueprintAttribute
from domain_classes.tree_node import ListNode, Node
from tests.unit.mock_data.mock_recipe_provider import MockStorageRecipeProvider
from tests.unit.tree_functionality.mock_data_for_tree_tests.get_node_for_tree_tests import (
    get_engine_package_node,
)
from tests.unit.tree_functionality.mock_data_for_tree_tests.mock_document_service_for_tree_tests import (
    mock_document_service,
)


# https://stackoverflow.com/questions/6027558/flatten-nested-dictionaries-compressing-keys
def flatten_dict(dd, separator="_", prefix=""):
    return (
        {
            prefix + separator + k if prefix else k: v
            for kk, vv in dd.items()
            for k, v in flatten_dict(vv, separator, kk).items()
        }
        if isinstance(dd, dict)
        else {prefix: dd}
    )


class TreenodeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_storage_recipe_provider = MockStorageRecipeProvider(
            path_to_mock_storage_recipes="src/tests/unit/mock_data/mock_storage_recipes/mock_storage_recipes.json"
        ).provider

    def test_is_root(self):
        root_data = {"_id": 1, "name": "root", "description": "", "type": "all_contained_cases_blueprint"}
        root = Node(
            key="root",
            uid="1",
            entity=root_data,
            blueprint_provider=mock_document_service.get_blueprint,
            attribute=BlueprintAttribute(name="", attribute_type="all_contained_cases_blueprint"),
            recipe_provider=self.mock_storage_recipe_provider,
        )

        nested_data = {"name": "Nested", "description": "", "type": "Garden"}
        nested = Node(
            key="nested",
            uid="",
            entity=nested_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=root,
            attribute=BlueprintAttribute(name="", attribute_type="Garden"),
            recipe_provider=self.mock_storage_recipe_provider,
        )

        assert root.is_root()
        assert not nested.is_root()

    def test_replace(self):
        root_data = {"_id": 1, "name": "root", "description": "", "type": "all_contained_cases_blueprint"}
        root = Node(
            key="",
            uid="1",
            entity=root_data,
            blueprint_provider=mock_document_service.get_blueprint,
            attribute=BlueprintAttribute(name="", attribute_type="all_contained_cases_blueprint"),
            recipe_provider=self.mock_storage_recipe_provider,
        )

        nested_1_data = {"name": "Nested1", "description": "", "type": "Garden"}
        nested_1 = Node(
            key="nested",
            uid="",
            entity=nested_1_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=root,
            attribute=BlueprintAttribute(name="", attribute_type="Garden"),
            recipe_provider=self.mock_storage_recipe_provider,
        )

        nested_2_data = {"name": "Nested2", "description": "", "type": "Garden"}
        nested_2 = Node(
            key="nested",
            uid="",
            entity=nested_2_data,
            blueprint_provider=mock_document_service.get_blueprint,
            attribute=BlueprintAttribute(name="", attribute_type="Garden"),
            recipe_provider=self.mock_storage_recipe_provider,
        )

        actual_before = {
            "_id": "1",
            "name": "root",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {"name": "Nested1", "description": "", "type": "Garden"},
        }

        assert actual_before == tree_node_to_dict(root)

        root.replace("1.nested", nested_2)

        actual_after_replaced = {
            "_id": "1",
            "name": "root",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {"name": "Nested2", "description": "", "type": "Garden"},
        }

        assert actual_after_replaced == tree_node_to_dict(root)

    def test_depth(self):
        root_data = {"_id": 1, "name": "root", "description": "", "type": "all_contained_cases_blueprint"}
        root = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="root",
            uid="1",
            entity=root_data,
            blueprint_provider=mock_document_service.get_blueprint,
            attribute=BlueprintAttribute(name="", attribute_type="all_contained_cases_blueprint"),
        )

        nested_data = {"name": "Nested", "description": "", "type": "Garden"}
        nested = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="nested",
            uid="",
            entity=nested_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=root,
            attribute=BlueprintAttribute(name="", attribute_type="Garden"),
        )

        assert root.depth() == 0
        assert nested.depth() == 1

    # TODO i have no idea how traverse() is supposed to wrok.
    def test_traverse(self):
        document_1 = {
            "_id": "parent",
            "name": "Parent",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {
                "name": "Nested1",
                "description": "",
                "type": "Garden",
                "nested": {
                    "name": "My_Best_Bush",
                    "description": "",
                    "type": "Bush",
                    "reference": {"address": "$3", "type": "dmss://system/SIMOS/Reference", "referenceType": "link"},
                },
            },
        }

        root = tree_node_from_dict(
            document_1,
            mock_document_service.get_blueprint,
            uid=document_1.get("_id"),
            recipe_provider=self.mock_storage_recipe_provider,
        )
        result = [node.node_id for node in root.traverse()]
        expected = [
            "parent",
            "parent.nested",
            "parent.nested.nested",
            "parent.nested.nested.reference",
            "",
            ".nested",
            "parent.references",
        ]

        assert result == expected

    def test_traverse_reverse(self):
        root_data = {"_id": 1, "name": "root", "description": "", "type": "all_contained_cases_blueprint"}
        root = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="root",
            uid="1",
            entity=root_data,
            blueprint_provider=mock_document_service.get_blueprint,
            attribute=BlueprintAttribute(name="", attribute_type="all_contained_cases_blueprint"),
        )

        nested_data = {"name": "Nested1", "description": "", "type": "Garden"}
        nested = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="nested",
            uid="",
            entity=nested_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=root,
            attribute=BlueprintAttribute(name="", attribute_type="Garden"),
        )

        nested_2_data = {"name": "Nested2", "description": "", "type": "Bush"}
        nested_2 = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="nested",
            uid="",
            entity=nested_2_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=nested,
            attribute=BlueprintAttribute(name="", attribute_type="Bush"),
        )

        result = [node.entity["name"] for node in nested_2.traverse_reverse()]
        expected = ["Nested2", "Nested1", "root"]
        assert result == expected

    def test_node_id(self):
        root_data = {"_id": 1, "name": "root", "description": "", "type": "all_contained_cases_blueprint"}
        root = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="",
            uid="1",
            entity=root_data,
            blueprint_provider=mock_document_service.get_blueprint,
            attribute=BlueprintAttribute(name="", attribute_type="all_contained_cases_blueprint"),
        )

        nested_data = {"name": "Nested", "description": "", "type": "Garden"}
        nested = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="nested",
            uid="",
            entity=nested_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=root,
            attribute=BlueprintAttribute(name="", attribute_type="Garden"),
        )

        nested_2_data = {"name": "Nested", "description": "", "type": "Bush"}
        nested_2 = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="nested",
            uid="",
            entity=nested_2_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=nested,
            attribute=BlueprintAttribute(name="", attribute_type="Bush"),
        )

        nested_2_reference_data = {"_id": "2", "name": "Reference", "description": "", "type": "Garden"}
        reference = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="reference",
            uid="2",
            entity=nested_2_reference_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=nested_2,
            attribute=BlueprintAttribute(name="", attribute_type="Garden"),
        )

        list_data = {"name": "List", "type": "Bush"}
        list_node = ListNode(
            recipe_provider=self.mock_storage_recipe_provider,
            key="list",
            uid="",
            entity=list_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=root,
            attribute=BlueprintAttribute(name="", attribute_type="Bush"),
        )

        item_1_data = {"name": "Item1", "description": "", "type": "Garden"}
        item_1 = Node(
            recipe_provider=self.mock_storage_recipe_provider,
            key="0",
            uid="",
            entity=item_1_data,
            blueprint_provider=mock_document_service.get_blueprint,
            parent=list_node,
            attribute=BlueprintAttribute(name="", attribute_type="Garden"),
        )

        assert root.node_id == "1"
        assert nested.node_id == "1.nested"
        assert nested_2.node_id == "1.nested.nested"
        assert nested_2.node_id == "1.nested.nested"
        assert reference.node_id == "1.nested.nested.reference"
        assert list_node.node_id == "1.list"
        assert item_1.node_id == "1.list.0"

    def test_search(self):
        document_1 = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {
                "name": "Nested",
                "description": "",
                "type": "Garden",
                "nested": {
                    "name": "Nested",
                    "description": "",
                    "type": "Bush",
                    "reference": {"_id": "2", "name": "Reference", "description": "", "type": "Garden"},
                },
                "reference": {},
                "references": [],
            },
        }

        root = tree_node_from_dict(
            document_1,
            mock_document_service.get_blueprint,
            uid=document_1.get("_id"),
            recipe_provider=self.mock_storage_recipe_provider,
        )

        child_1 = root.search("1.nested.nested")

        assert child_1.node_id == "1.nested.nested"

        child_2 = root.search("1.nested.nested.reference")

        assert child_2.node_id == "1.nested.nested.reference"

    def test_get_by_keys(self):
        document_1 = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {
                "name": "Nested",
                "description": "",
                "type": "Garden",
                "nested": {
                    "name": "Nested",
                    "description": "",
                    "type": "Bush",
                    "reference": {"_id": "2", "name": "Reference", "description": "", "type": "Garden"},
                },
            },
        }

        root = tree_node_from_dict(
            document_1,
            mock_document_service.get_blueprint,
            uid=document_1.get("_id"),
            recipe_provider=self.mock_storage_recipe_provider,
        )

        child_1 = root.get_by_path(["nested", "nested"])

        assert child_1.node_id == "1.nested.nested"

        child_2 = root.get_by_path(["nested", "nested", "reference"])

        assert child_2.uid == "2"

    def test_update(self):
        document_1 = {
            "_id": "1",
            "name": "Parent",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {
                "name": "Nested",
                "description": "",
                "type": "Garden",
                "nested": {
                    "name": "Nested",
                    "description": "",
                    "type": "Bush",
                    "reference": {"_id": "2", "name": "Reference", "description": "", "type": "Garden"},
                },
            },
            "reference": {"_id": "2", "name": "a_reference", "type": "Garden"},
            "references": [],
        }

        root = tree_node_from_dict(
            document_1,
            mock_document_service.get_blueprint,
            uid=document_1.get("_id"),
            recipe_provider=self.mock_storage_recipe_provider,
        )

        update_0 = {
            "name": "New-name",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {
                "name": "Nested",
                "description": "Some description",
                "type": "Garden",
                "nested": {
                    "name": "Nested",
                    "description": "",
                    "type": "Bush",
                    "reference": {"_id": "2", "name": "Reference", "description": "", "type": "Garden"},
                },
            },
            "reference": {"_id": "2", "name": "a_reference", "type": "Garden"},
            "references": [],
        }

        root.update(update_0)

        assert get_and_print_diff(tree_node_to_dict(root), {**update_0, "_id": "1"}) == []

        update_1 = {
            "name": "New-name",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {
                "name": "Nested",
                "description": "Some description",
                "type": "Garden",
                "nested": {
                    "name": "New-name",
                    "description": "",
                    "type": "Bush",
                    "reference": {"_id": "2", "name": "Reference", "description": "", "type": "Garden"},
                },
            },
            "reference": {"_id": "2", "name": "a_reference", "type": "Garden"},
            "references": [],
        }

        root.update(update_1)

        assert get_and_print_diff(tree_node_to_dict(root), {**update_1, "_id": "1"}) == []

        update_2 = {
            "name": "New-name",
            "description": "",
            "type": "all_contained_cases_blueprint",
            "nested": {
                "name": "Nested",
                "description": "Some description",
                "type": "Garden",
                "nested": {
                    "name": "New-name",
                    "description": "",
                    "type": "Bush",
                    "reference": {"_id": "2", "name": "New-name", "description": "", "type": "Garden"},
                },
            },
            "reference": {"_id": "2", "name": "a_reference", "type": "Garden"},
            "references": [],
        }

        root.update(update_2)

        assert get_and_print_diff(tree_node_to_dict(root), {**update_2, "_id": "1"}) == []

        expected = {
            "_id": "1",
            "name": "New-name",
            "type": "all_contained_cases_blueprint",
            "description": "",
            "nested": {
                "name": "Nested",
                "type": "Garden",
                "description": "Some description",
                "nested": {
                    "name": "New-name",
                    "type": "Bush",
                    "description": "",
                    "reference": {"_id": "2", "name": "New-name", "type": "Garden", "description": ""},
                },
            },
            "reference": {"_id": "2", "name": "a_reference", "type": "Garden"},
            "references": [],
        }

        # reference and nested.nested.reference has uid and id generated since the tree now includes
        # nodes when attributes are missing, needed for having error nodes in the index.

        expected_flat = flatten_dict(expected)
        actual_flat = flatten_dict(tree_node_to_dict(root))
        # less than only works on flat dictionaries.
        assert expected_flat.items() <= actual_flat.items()

    def test_is_storage_contained(self):
        engine_package_node = get_engine_package_node()
        engine_ref_node = engine_package_node.children[0].children[0]

        assert engine_ref_node.storage_contained is True
        assert engine_ref_node.parent.storage_recipes[0].is_contained(engine_ref_node.attribute.name) is True
