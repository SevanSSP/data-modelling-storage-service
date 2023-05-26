from typing import Union

from common.utils.data_structure.find import find
from enums import REFERENCE_TYPES, SIMOS
from storage.data_source_class import DataSource


def delete_list_recursive(value: Union[list, dict], data_source: DataSource):
    """
    Digs down in any list (simple, matrix, complex), and delete any contained referenced documents
    """
    if isinstance(value, list):
        [delete_list_recursive(item, data_source) for item in value]
    elif isinstance(value, dict):
        delete_dict_recursive(value, data_source)


def delete_by_attribute_path(document: dict, path: list[str], data_source: DataSource, get_data_source) -> dict:
    path_elements = [e.strip("[]./") for e in path]
    # Step through all the path items except the last one that should be deleted
    target = find(document, path_elements[:-1])

    if isinstance(target, list):
        delete_dict_recursive(target[int(path_elements[-1])], data_source=data_source)
        del target[int(path_elements[-1])]
    else:
        delete_dict_recursive(target[path_elements[-1]], data_source=data_source)
        del target[path_elements[-1]]

    return document


def delete_dict_recursive(in_dict: dict, data_source: DataSource):
    if (
        in_dict.get("type") == SIMOS.REFERENCE.value and in_dict.get("referenceType") == REFERENCE_TYPES.STORAGE.value
    ):  # It's a model contained reference
        delete_document(data_source, in_dict["address"])
    elif in_dict.get("type") == SIMOS.BLOB.value:
        data_source.delete_blob(in_dict["_blob_id"])
    else:
        for value in in_dict.values():
            if isinstance(value, dict) or isinstance(value, list):  # Potentially complex
                if not value:
                    continue
                if isinstance(value, list):
                    delete_list_recursive(value, data_source)
                else:
                    delete_dict_recursive(value, data_source)


def delete_document(data_source: DataSource, document_id: str):
    """
    Delete a document, and any model contained children.
    """
    if document_id.startswith("$"):
        document_id = document_id[1:]
    document: dict = data_source.get(document_id)
    delete_dict_recursive(document, data_source)
    data_source.delete(document_id)
