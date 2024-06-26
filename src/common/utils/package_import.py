import json
import os
from uuid import uuid4

from authentication.models import User
from common.address import Address
from common.exceptions import BadRequestException, NotFoundException
from common.providers.address_resolver.address_resolver import (
    ResolvedAddress,
    resolve_address,
)
from common.utils.logging import logger
from common.utils.string_helpers import url_safe_name
from enums import REFERENCE_TYPES, SIMOS
from storage.data_source_interface import DataSource
from storage.internal.get_data_source_cached import get_data_source_cached


def _add_documents(path, documents, data_source) -> list[dict]:
    docs = []
    for file in documents:
        logger.debug(f"Working on {file}...")
        with open(f"{path}/{file}") as json_file:
            document = json.load(json_file)
        if document.get("name") and not url_safe_name(document["name"]):
            raise BadRequestException(
                message=f"'{document['name']}' is a invalid document name. "
                f"Only alphanumeric, underscore, and dash are allowed characters"
            )
        document["_id"] = document.get("_id", str(uuid4()))
        data_source.update(document)
        docs.append(
            {
                "address": f"${document['_id']}",
                "type": SIMOS.REFERENCE.value,
                "referenceType": REFERENCE_TYPES.STORAGE.value,
            }
        )

    return docs


def import_package(path: str, user: User, data_source_name: str, is_root: bool = False) -> dict:
    data_source: DataSource = get_data_source_cached(data_source_id=data_source_name, user=user)
    package = {
        "name": os.path.basename(path),
        "type": SIMOS.PACKAGE.value,
        "isRoot": is_root,
    }
    try:
        resolved_address: ResolvedAddress = resolve_address(
            Address(package["name"], data_source.name),
            lambda data_source_name: get_data_source_cached(data_source_name, user),
        )
        if resolved_address.entity:
            raise BadRequestException(
                message=(
                    f"A root package with name '{package['name']}' "
                    "already exists in data source '{data_source.name}'"
                )
            )
    except NotFoundException:
        pass

    files = []
    directories = []

    for _, directory, file in os.walk(path):
        directories.extend(directory)
        files.extend(file)
        break

    package["content"] = _add_documents(path, files, data_source)
    for folder in directories:
        package["content"].append(
            import_package(f"{path}/{folder}", user, is_root=False, data_source_name=data_source.name)
        )

    data_source.update(package)
    logger.info(f"Imported package {package['name']}")
    return {
        "address": f"${package['_id']}",
        "type": SIMOS.REFERENCE.value,
        "referenceType": REFERENCE_TYPES.STORAGE.value,
    }
