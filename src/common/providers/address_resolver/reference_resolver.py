import json
from collections.abc import Callable

from common.address import Address
from common.entity.is_reference import is_reference
from common.exceptions import ApplicationException, NotFoundException
from common.providers.address_resolver.address_resolver import (
    ResolvedAddress,
    resolve_address,
)
from storage.data_source_class import DataSource


def _resolve_reference_list(
    values: list,
    document_repository: DataSource,
    get_data_source,
    current_id,
    depth: int = 1,
    depth_count: int = 0,
    path: list[str] | None = None,
    cache: dict | None = None,
) -> list:
    if not values:  # Return an empty list
        return values

    value_sample = values[0]

    if isinstance(value_sample, list):  # Call recursively for nested lists
        return [
            _resolve_reference_list(
                value, document_repository, get_data_source, current_id, depth, depth_count, path, cache
            )
            for value in values
        ]

    if is_reference(value_sample):
        return [
            _get_complete_sys_document(
                value, document_repository, get_data_source, current_id, depth, depth_count, path, cache
            )
            for value in values
        ]

    if isinstance(value_sample, dict):
        if path:
            return [
                resolve_references_in_entity(
                    value,
                    document_repository,
                    get_data_source,
                    current_id,
                    depth,
                    depth_count,
                    path[:-1] + [f"{path[-1]}", f"[{index}]"],
                    cache,
                )
                for index, value in enumerate(values)
            ]

    # Values are primitive, return as is.
    return values


def _get_complete_sys_document(
    reference: dict,
    data_source: DataSource,
    get_data_source,
    current_id: str | None = None,
    depth: int = 1,
    depth_count: int = 0,
    path: list[str] | None = None,
    cache: dict | None = None,
) -> dict | list:
    if not reference["address"]:
        raise ApplicationException("Invalid link. Missing 'address'", data=reference)

    if cache is not None and f"{data_source.name}::{reference["address"]}" in cache:
        return cache[f"{data_source.name}::{reference["address"]}"]

    address = Address.from_relative(reference["address"], current_id, data_source.name, path)

    try:
        resolved_address: ResolvedAddress = resolve_address(address, get_data_source, cache)
    except NotFoundException as ex:
        raise NotFoundException(
            message=f"Could not resolve address '{reference['address']}'",
            debug=f"Reference: {json.dumps(reference)}, DocumentId: {current_id}",
            data=ex.dict(),
        ) from ex

    if is_reference(resolved_address.entity):
        resolved_address = resolve_address(
            Address.from_relative(
                resolved_address.entity["address"], resolved_address.document_id, resolved_address.data_source_id, path
            ),
            get_data_source,
        )

    # For supporting ^ references, update the current document id
    if "_id" in resolved_address.entity:
        current_id = resolved_address.entity["_id"]
        path = []

    resolved_entity = resolve_references_in_entity(
        resolved_address.entity,
        get_data_source(address.data_source),
        get_data_source,
        current_id,
        depth,
        depth_count,
        path,
        cache,
    )
    if cache is not None:
        cache[f"{address.data_source}::{address.path}"] = resolved_entity
    return resolved_entity


def resolve_references_in_entity(
    entity: dict | list,
    data_source: DataSource,
    get_data_source: Callable,
    current_id: str | None,
    depth: int,
    depth_count: int,
    path: list[str] | None = None,
    cache: dict | None = None,
) -> dict | list:
    """
    Resolve references inside an entity.

    Resolving a reference means that a link or storage reference object (of type Reference) is substituted by the full document it refers to (defined in the address part of the reference object).
    The depth parameter determines how far down into the document we want to resolve references.
    """
    if not path:
        path = []

    if depth <= depth_count:
        if depth_count >= 999:
            raise RecursionError("Reached max-nested-depth (999). Most likely some recursive entities")
        return entity

    if isinstance(entity, list):
        entity = _resolve_reference_list(entity, data_source, get_data_source, current_id, depth, depth_count + 1, path)
    else:
        for key, value in entity.items():
            if not value:
                continue

            if isinstance(value, list):  # If it's a list, resolve any references
                entity[key] = _resolve_reference_list(
                    value, data_source, get_data_source, current_id, depth, depth_count + 1, [*path, key], cache
                )
            elif isinstance(value, dict):
                if is_reference(value):
                    entity[key] = _get_complete_sys_document(
                        value, data_source, get_data_source, current_id, depth, depth_count + 1, [*path, key], cache
                    )
                else:
                    entity[key] = resolve_references_in_entity(
                        value, data_source, get_data_source, current_id, depth, depth_count + 1, [*path, key], cache
                    )
    return entity
