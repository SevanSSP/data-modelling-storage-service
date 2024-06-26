from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, PlainTextResponse

from authentication.authentication import auth_w_jwt_or_pat
from authentication.models import AccessControlList, User
from common.address import Address
from common.providers.storage_recipe_provider import storage_recipe_provider
from common.responses import create_response, responses
from services.document_service.document_service import DocumentService
from storage.internal.data_source_repository import DataSourceRepository

from .use_cases.get_acl_use_case import get_acl_use_case
from .use_cases.set_acl_use_case import set_acl_use_case

router = APIRouter(tags=["default", "access_control"], prefix="/acl")


@router.put(
    "/{address:path}",
    operation_id="set_acl",
    response_model=str,
    responses=responses,
)
@create_response(PlainTextResponse)
def set_acl(
    address: str,
    acl: AccessControlList,
    recursively: bool = True,
    user: User = Depends(auth_w_jwt_or_pat),
):
    """Update access control list (ACL) for a document.

    Args:
    - data_source_id (str): The ID of the data source which the document resides in.
    - document_id (str): The ID of the document for which to set the ACL.
    - acl (ACL): An access control list.
    - user (User): The authenticated user accessing the endpoint, automatically generated from provided bearer token or Access-Key.

    Returns:
    - str: "OK" (200)
    """
    address_obj = Address.from_absolute(address)
    document_service = DocumentService(
        user=user,
        recipe_provider=storage_recipe_provider,
    )

    return set_acl_use_case(
        data_source_id=address_obj.data_source,
        document_id=address_obj.path,
        acl=acl,
        recursively=recursively,
        data_source_repository=DataSourceRepository(user),
        document_service=document_service,
    )


@router.get(
    "/{address:path}",
    operation_id="get_acl",
    response_model=AccessControlList,
    responses=responses,
)
@create_response(JSONResponse)
def get_acl(address: str, user: User = Depends(auth_w_jwt_or_pat)):
    """GET the access control list (ACL) for a document.

    The ACL determines which access a given user has for a document (Read, Write or None).

    Args:
    - data_source_id (str): The ID of the data source which the document resides in.
    - document_id (str): The ID of the document for which to check the ACL.
    - user (User): The authenticated user accessing the endpoint, automatically generated from provided bearer token or Access-Key.

    Returns:
    - ACL: The access control list requested.
    """
    address_obj = Address.from_absolute(address)
    return get_acl_use_case(
        data_source_id=address_obj.data_source,
        document_id=address_obj.path,
        data_source_repository=DataSourceRepository(user),
    ).to_dict()
