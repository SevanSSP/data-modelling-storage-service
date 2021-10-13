import json

from behave import given

from authentication.access_control import ACL
from domain_classes.blueprint_attribute import BlueprintAttribute
from domain_classes.tree_node import ListNode, Node
from enums import DMT, SIMOS
from services.document_service import DocumentService
from storage.internal.data_source_repository import get_data_source
from storage.internal.data_source_repository import DataSourceRepository
from utils.create_entity import CreateEntity
from services.database import data_source_collection

document_service = DocumentService(get_data_source)


def generate_tree_from_rows(node: Node, rows):
    if len(rows) == 0:
        return node

    if node.type == DMT.PACKAGE.value:
        content_node = node.search(f"{node.node_id}.content")
        # Create content not if not exists
        if not content_node:
            data = {"name": "content", "type": DMT.PACKAGE.value, "attributeType": SIMOS.BLUEPRINT_ATTRIBUTE.value}
            content_node = ListNode(
                key="content",
                uid="",
                entity=data,
                blueprint_provider=document_service.get_blueprint,
                attribute=BlueprintAttribute("content", DMT.ENTITY.value),
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
                attribute=BlueprintAttribute("content", child_data["type"]),
            )

            print(f"adding {child_node.node_id} to {node.node_id}")
            content_node.add_child(child_node)

            if child_node.type == DMT.PACKAGE.value:
                filtered = list(filter(lambda i: i["uid"] != node.uid, rows))
                generate_tree_from_rows(child_node, filtered)

    return node


def generate_tree(data_source_id: str, table):
    root = Node(
        key=data_source_id, attribute=BlueprintAttribute(data_source_id, DMT.DATASOURCE.value), uid=data_source_id
    )
    root_package = list(filter(lambda row: row["parent_uid"] == "", table.rows))[0]
    if not root_package:
        raise Exception("Root package is not found, you need to specify root package")
    root_package_data = root_package.as_dict()
    root_package_data["isRoot"] = True
    root_package_node = Node(
        key="root",
        uid=root_package["uid"],
        entity=root_package_data,
        blueprint_provider=document_service.get_blueprint,
        parent=root,
        attribute=BlueprintAttribute("root", DMT.PACKAGE.value),
    )
    rows = list(filter(lambda row: row["parent_uid"] != "", table.rows))
    generate_tree_from_rows(root_package_node, rows)
    return root_package_node


@given('there are documents for the data source "{data_source_id}" in collection "{collection}"')
def step_impl_documents(context, data_source_id: str, collection: str):
    context.documents = {}
    tree: Node = generate_tree(data_source_id, context.table)
    tree.show_tree()
    document_service = DocumentService(repository_provider=get_data_source)
    document_service.save(node=tree, data_source_id=data_source_id)


@given('AccessControlList for document "{document_id}" in data-source "{data_source}" is')
def step_impl(context, document_id, data_source):
    acl = ACL(**json.loads(context.text))
    document_service.repository_provider(data_source).update_access_control(document_id, acl)


@then('AccessControlList for document "{document_id}" in data-source "{data_source}" should be')
def step_impl(context, document_id, data_source):
    acl = ACL(**json.loads(context.text))
    lookup_for_data_source: dict = {}

    mongodb_cursor = data_source_collection.find({"_id": data_source})
    for document in mongodb_cursor:
        lookup_for_data_source = {"documentLookUp": document["documentLookUp"]}
    actual_acl_as_json: dict = lookup_for_data_source["documentLookUp"][document_id]["acl"]

    if actual_acl_as_json != acl.dict():
        raise Exception(
            f"expected ACL not equal to actual ACL! \nExpected: {json.dumps(acl.dict())}\n\nActual: {json.dumps(actual_acl_as_json)} "
        )


@given('AccessControlList for data-source "{data_source}" is')
def step_impl(context, data_source):
    acl = ACL(**json.loads(context.text))
    DataSourceRepository().update_access_control(data_source, acl)
