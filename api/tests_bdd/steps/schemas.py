import json

from behave import given

from classes.data_source import DataSource
from classes.dto import DTO
from core.repository import Repository
from core.repository.repository_factory import get_repository
from config import Config
from utils.package_import import import_package


@given("data modelling tool templates are imported")
def step_impl(context):
    for folder in Config.SYSTEM_FOLDERS:
        import_package(f"{Config.APPLICATION_HOME}/core/{folder}", collection=Config.SYSTEM_COLLECTION, is_root=True)


@given('there exist document with id "{uid}" in data source "{data_source_id}"')
def step_impl_2(context, uid: str, data_source_id: str):
    data_source = DataSource(uid=data_source_id)
    document: DTO = DTO(uid=uid, data=json.loads(context.text))
    document_repository: Repository = get_repository(data_source)
    document_repository.add(document)
