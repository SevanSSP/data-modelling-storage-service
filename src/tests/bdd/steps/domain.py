import json

from behave import given, then

from authentication.models import AccessControlList
from common.providers.storage_recipe_provider import storage_recipe_provider
from common.tree.tree_node import ListNode, Node
from domain_classes.blueprint_attribute import BlueprintAttribute
from enums import SIMOS, BuiltinDataTypes
from features.entity.use_cases.instantiate_entity_use_case.create_entity import CreateEntity
from services.database import acl_lookup_db
from services.document_service.document_service import DocumentService
from storage.internal.data_source_repository import DataSourceRepository


def generate_tree_from_rows(node: Node, rows, document_service):
    if len(rows) == 0:
        return node

    if node.type == SIMOS.PACKAGE.value:
        content_node = node.search(f"{node.node_id}.content")
        # Create content not if not exists
        if not content_node:
            data = {
                "name": "content",
                "type": SIMOS.PACKAGE.value,
                "attributeType": SIMOS.BLUEPRINT_ATTRIBUTE.value,
            }
            content_node = ListNode(
                key="content",
                uid="",
                entity=data,
                blueprint_provider=document_service.get_blueprint,
                recipe_provider=node.recipe_provider,
                attribute=BlueprintAttribute(name="content", attribute_type=BuiltinDataTypes.OBJECT.value),
            )
            node.add_child(content_node)
    else:
        content_node = node

    for row in rows:
        # Add children (only to packages)
        if row["parent_uid"] == node.uid:
            child_data = row.as_dict()
            entity = CreateEntity(document_service.get_blueprint, child_data["type"]).entity
            entity["name"] = child_data["name"]
            child_node = Node(
                key="",
                uid=child_data["uid"],
                entity=entity,
                blueprint_provider=document_service.get_blueprint,
                recipe_provider=node.recipe_provider,
                attribute=BlueprintAttribute(name="content", attribute_type=child_data["type"]),
            )

            print(f"adding {child_node.node_id} to {node.node_id}")
            content_node.add_child(child_node)

            if child_node.type == SIMOS.PACKAGE.value:
                filtered = list(filter(lambda i: i["uid"] != node.uid, rows))
                generate_tree_from_rows(child_node, filtered, document_service)

    return node


def generate_tree(data_source_id: str, table, document_service):
    root = Node(
        key=data_source_id,
        attribute=BlueprintAttribute(name=data_source_id, attribute_type=SIMOS.DATASOURCE.value),
        uid=data_source_id,
    )
    root_package = next(filter(lambda row: row["parent_uid"] == "", table.rows))
    if not root_package:
        raise Exception("Root package is not found, you need to specify root package")
    root_package_data = root_package.as_dict()
    root_package_data["isRoot"] = True
    root_package_node = Node(
        key="root",
        uid=root_package["uid"],
        entity=root_package_data,
        blueprint_provider=document_service.get_blueprint,
        recipe_provider=storage_recipe_provider,
        parent=root,
        attribute=BlueprintAttribute(name="root", attribute_type=SIMOS.PACKAGE.value),
    )
    rows = list(filter(lambda row: row["parent_uid"] != "", table.rows))
    generate_tree_from_rows(root_package_node, rows, document_service)
    return root_package_node


@given('there are documents for the data source "{data_source_id}" in collection "{collection}"')
def step_impl_documents(context, data_source_id: str, collection: str):
    context.documents = {}
    document_service = DocumentService(user=context.user)
    tree: Node = generate_tree(data_source_id, context.table, document_service)
    tree.show_tree()
    for node in tree.traverse():
        if not node.storage_contained and not node.is_array():
            document_service.save(node=node, data_source_id=data_source_id)


@given('AccessControlList for document "{document_id}" in data-source "{data_source}" is')
def step_ACL_for_docs_in_DS_is(context, document_id, data_source):
    document_service = DocumentService(user=context.user)
    acl = AccessControlList(**json.loads(context.text))
    document_service.repository_provider(data_source, context.user).update_access_control(document_id, acl)


@then('AccessControlList for document "{document_id}" in data-source "{data_source}" should be')
def step_ACL_for_docs_in_DS_should_be(context, document_id, data_source):
    acl = AccessControlList(**json.loads(context.text))
    actual_acl_as_json: dict = acl_lookup_db.get(f"{data_source}:{document_id}")["acl"]

    if actual_acl_as_json != acl.to_dict():
        raise Exception(
            f"expected ACL not equal to actual ACL! \nExpected: {json.dumps(acl.to_dict())}\n\n"
            + f"Actual: {json.dumps(actual_acl_as_json)} "
        )


@given('AccessControlList for data-source "{data_source}" is')
def step_ACL_for_DS_is(context, data_source):
    acl = AccessControlList(**json.loads(context.text))
    DataSourceRepository(context.user).update_access_control(data_source, acl)
