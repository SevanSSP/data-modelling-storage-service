import re
from dataclasses import dataclass
from typing import Any, Callable, Tuple, Union

from common.address import Address
from common.exceptions import ApplicationException, NotFoundException
from common.utils.data_structure.find import find
from common.utils.data_structure.has_key_value_pairs import has_key_value_pairs
from common.utils.is_reference import is_reference
from storage.data_source_class import DataSource


def split_reference(reference: str) -> list[str]:
    """Splits a reference into it's string components
    e.g. "$123.content[1]" -> ["$123", ".content", "[1]"]"""
    parts = []
    remaining_ref = reference
    while remaining_ref:
        if remaining_ref[0] in "./":
            prefix_delim = remaining_ref[0]
            content = re.split(r"[./\[(]", remaining_ref, 2)[1]
            parts.append(f"{prefix_delim}{content}")
            remaining_ref = remaining_ref.removeprefix(parts[-1])
            continue
        if remaining_ref[0] in "[(":
            prefix_delim = remaining_ref[0]
            closing_bracket = "]" if prefix_delim == "[" else ")"
            content = re.split("[" + re.escape(f"{closing_bracket}") + "]", remaining_ref, 2)[0][1:]
            parts.append(f"{prefix_delim}{content}{closing_bracket}")
            remaining_ref = remaining_ref.removeprefix(parts[-1])
            continue

        content = re.split(r"[./]", remaining_ref, 1)[0]
        remaining_ref = remaining_ref.removeprefix(content)
        parts.append(content)
    return parts


def _next_reference_part(reference: str) -> Tuple[str, Union[str, None], str]:
    """Utility to get next reference part."""
    content = reference  # Default to reference
    deliminator = None
    remaining_reference = ""

    search = re.search(r"[.|/|\]|\[]", reference)  # Search for next deliminator
    if search:
        deliminator = search.group(0)
        # Extract the content (the text between the two deliminators)
        content = reference[: search.end() - 1]
        # Remove the extracted content (including deliminator), so that we don't handle it again.
        remaining_reference = reference[search.end() :]
    return content, deliminator, remaining_reference


@dataclass
class IdItem:
    """Points to an id."""

    id: str

    def get_entry_point(self, data_source: DataSource) -> Tuple[dict, str]:
        # Get the document from the data source
        result = data_source.get(self.id)
        if not result:
            raise NotFoundException(
                f"No document with id '{self.id}' could be found in data source '{data_source.name}'."
            )
        return result, self.id

    def __repr__(self):
        return f"${self.id}"


@dataclass
class QueryItem:
    """Query a list for a document."""

    def __repr__(self):
        return f'Query="{self.query_as_str}"'

    def __init__(self, query: str):
        self.query_as_str = query

        self.query_as_dict: dict[str, Any] = {}
        for pair in self.query_as_str.split(","):
            key, value = pair.split("=")
            if value == "True" or value == "False":
                self.query_as_dict[key] = bool(value)
            else:
                self.query_as_dict[key] = value

    def get_entry_point(self, data_source: DataSource) -> Tuple[dict, str]:
        result: list[dict] = data_source.find(self.query_as_dict)
        if not result:
            raise NotFoundException(
                f"No document that match '{self.query_as_str}' could be found in data source '{data_source.name}'."
            )
        if len(result) > 2:
            raise ApplicationException(
                f"More than 1 document that match '{self.query_as_str}' was returned from DataSource. That should not happen..."
            )
        return result[0], result[0]["_id"]

    def get_child(
        self, entity: dict | list, document_id: str, data_source: DataSource, get_data_source: Callable
    ) -> Tuple[Any, str]:
        if isinstance(entity, dict) and is_reference(entity):
            resolved_ref = resolve_reference(
                Address.from_relative(entity["address"], document_id, data_source.name), get_data_source
            )
            entity = resolved_ref.entity
            document_id = resolved_ref.document_id

        # Search inside an existing document (need to resolve any references first before trying to compare against filter)
        elements = [
            resolve_reference(
                Address.from_relative(f["address"], document_id, data_source.name), get_data_source
            ).entity
            if is_reference(f)
            else f
            for f in entity
        ]  # Resolve any references
        for index, element in enumerate(elements):
            if isinstance(element, dict) and has_key_value_pairs(element, self.query_as_dict):
                return entity[index], f"[{index}]"
        raise NotFoundException(f"No object matches filter '{self.query_as_str}'", data={"elements": elements})


@dataclass
class AttributeItem:
    """Move into a key of an object or find an item in a list based on index position."""

    path: str

    def __repr__(self):
        return f'Attribute="{self.path}"'

    def get_child(
        self, entity: dict | list, document_id: str, data_source: DataSource, get_data_source: Callable
    ) -> tuple[Any, str]:
        if isinstance(entity, dict) and is_reference(entity):
            entity = resolve_reference(
                Address.from_relative(entity["address"], document_id, data_source.name), get_data_source
            ).entity
        try:
            result = find(entity, [self.path])
        except (IndexError, ValueError, KeyError):
            if isinstance(entity, dict):
                raise NotFoundException(
                    f"Invalid attribute '{self.path}'. Valid attributes are '{list(entity.keys())}'."
                )
            else:
                raise NotFoundException(f"Invalid index '{self.path}'. Valid indices are < {len(entity)}.")

        return result, self.path


def reference_to_reference_items(reference: str) -> list[AttributeItem | QueryItem | IdItem]:
    """Split up the reference into reference items.
    The reference used as input to this function should not include protocol or data source.
    """
    queries = re.findall(r"\(([^\)]+)\)", reference)
    if queries:
        # Split the reference into the pieces surrounding the queries and remove trailing [( and )]
        remaining_ref_parts = re.split("|".join([re.escape(q) for q in queries]), reference)
        remaining_ref_parts = list(map(lambda x: re.sub(r"\[?\($|^\)\]?", "", x), remaining_ref_parts))

        items = _reference_to_reference_items(remaining_ref_parts[0], [], None)
        for index, query in enumerate(queries):
            items.append(QueryItem(query=query))
            items = _reference_to_reference_items(remaining_ref_parts[index + 1], [*items], None)
        return items
    else:
        return _reference_to_reference_items(reference, [], None)


def _reference_to_reference_items(reference: str, items, prev_deliminator) -> list[AttributeItem | QueryItem | IdItem]:
    if len(reference) == 0:
        return items

    content, deliminator, remaining_reference = _next_reference_part(reference)
    if content == "":
        # If the original reference starts with a deliminator (e.g. /)
        # then there is no content.
        # The deliminator is extracted from the remaining reference.
        # Continue resolve the remaining reference.
        return _reference_to_reference_items(remaining_reference, items, deliminator)

    if "$" in content:  # By id
        items.append(IdItem(content[1:]))
    elif len(items) == 0:  # By root package
        items.append(QueryItem(query=f"name={content},isRoot=True"))
    elif prev_deliminator == "/":  # By package
        items.append(AttributeItem("content"))
        items.append(QueryItem(query=f"name={content}"))
    elif prev_deliminator == "[" and deliminator == "]":  # By list index
        items.append(AttributeItem(f"[{content}]"))
    elif prev_deliminator == ".":  # By attribute
        items.append(AttributeItem(content))
    else:
        raise Exception(f"Not supported reference format: {reference}")

    return _reference_to_reference_items(remaining_reference, items, deliminator)


def resolve_reference_items(
    data_source: DataSource,
    reference_items: list[AttributeItem | QueryItem | IdItem],
    get_data_source: Callable,
) -> tuple[list | dict, list[str]]:
    if len(reference_items) == 0 or isinstance(reference_items[0], AttributeItem):
        raise NotFoundException(f"Invalid reference_items {reference_items}.")
    entity, id = reference_items[0].get_entry_point(data_source)
    path = [id]
    for index, ref_item in enumerate(reference_items[1:]):
        if isinstance(ref_item, IdItem):
            raise NotFoundException(f"Invalid reference_items {reference_items}.")
        entity, attribute = ref_item.get_child(entity, path[0], data_source, get_data_source)
        if is_reference(entity) and index < len(reference_items) - 2:
            # Found a new document, use that as new starting point for the attribute path
            address = Address.from_relative(entity["address"], path[0], data_source.name)
            resolved_reference = resolve_reference(address, get_data_source)
            path = [resolved_reference.document_id, *resolved_reference.attribute_path]
        else:
            path.append(attribute)
        if not isinstance(entity, (list, dict)):
            raise NotFoundException(f"Path {path} leads to a primitive value.")
    return entity, path


@dataclass(frozen=True)
class ResolvedReference:
    data_source_id: str
    document_id: str
    attribute_path: list[str]
    entity: dict | list


def resolve_reference(address: Address, get_data_source: Callable) -> ResolvedReference:
    """Resolve the reference into a document."""
    if not address.path:
        raise ApplicationException("Failed to resolve reference. Got empty address path.")

    reference_items = reference_to_reference_items(address.path)

    # The first reference item should always be a DataSourceItem
    data_source = get_data_source(address.data_source)
    document, path = resolve_reference_items(data_source, reference_items, get_data_source)
    return ResolvedReference(
        entity=document,
        data_source_id=address.data_source,
        document_id=str(path[0]),
        attribute_path=path[1:],
    )
