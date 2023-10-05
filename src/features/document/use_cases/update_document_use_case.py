from typing import BinaryIO, List, Optional, Union

from fastapi import UploadFile

from common.address import Address
from common.entity.validators import validate_entity, validate_entity_against_self
from common.exceptions import NotFoundException, ValidationException
from common.tree.merge_entity_and_files import merge_entity_and_files
from common.tree.tree_node import Node
from common.tree.tree_node_serializer import tree_node_to_dict
from common.utils.logging import logger
from enums import SIMOS, BuiltinDataTypes
from services.document_service.document_service import DocumentService


def _update_document(
    address: Address,
    data: Union[dict, list],
    document_service: DocumentService,
    files: dict[str, BinaryIO] | None,
):
    """
    Update a document.

    What to update is referred to with an address.
    It can either be an entire document or just an attribute inside a document.
    """
    validate_entity_against_self(data, document_service.get_blueprint)
    if not address.path:
        raise Exception(f"Could not find the node on '{address}'")

    try:
        node: Node = document_service.get_document(address)  # type: ignore
    except NotFoundException:
        raise ValidationException(
            f"Can not update document with address {address}, since that document does not exist. If the goal is to add a document, use the document add use instead"
        )

    if node.attribute.attribute_type != BuiltinDataTypes.OBJECT.value:
        validate_entity(
            data,
            document_service.get_blueprint,
            document_service.get_blueprint(node.attribute.attribute_type),
            "extend",
        )
        # TODO consider validating link reference objects if the data parameter is of type system/SIMOS/Reference.

    node.update(data)
    if files:
        merge_entity_and_files(node, files)

    document_service.save(node, address.data_source, initial=True)
    logger.info(f"Updated entity '{address}'")
    return {"data": tree_node_to_dict(node)}


def update_document_use_case(
    address: Address,
    data: Union[dict, list],
    document_service: DocumentService,
    files: Optional[List[UploadFile]] = None,
):
    """Update document.

    Args:
        address: Reference to an existing entity
        data: The data to be updated
        document_service: The document service
        files: Dict with names and files of the files contained in the document
    Returns:
        A dict that contains the updated document.
    """

    document = _update_document(
        address=address,
        data=data,
        document_service=document_service,
        files={f.filename: f.file for f in files} if files else None,
    )
    # Do not invalidate the blueprint cache if it was not a blueprint that was changed
    if "type" in document["data"] and document["data"]["type"] == SIMOS.BLUEPRINT.value:
        document_service.invalidate_cache()
    return document
