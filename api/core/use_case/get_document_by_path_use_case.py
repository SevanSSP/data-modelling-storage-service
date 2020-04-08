from api.core.enums import PRIMITIVES
from api.core.repository.repository_factory import get_repository
from api.core.service.document_service import DocumentService
from api.core.shared import request_object as req
from api.core.shared import response_object as res
from api.core.shared import use_case as uc
from api.core.utility import get_document_by_ref

from api.classes.blueprint_attribute import BlueprintAttribute
from api.classes.dto import DTO
from api.utils.logging import logger


class GetDocumentByPathRequestObject(req.ValidRequestObject):
    def __init__(self, data_source_id, path, ui_recipe, attribute):
        self.data_source_id = data_source_id
        self.path = path
        self.ui_recipe = ui_recipe
        self.attribute = attribute

    @classmethod
    def from_dict(cls, adict):
        invalid_req = req.InvalidRequestObject()

        if "data_source_id" not in adict:
            invalid_req.add_error("data_source_id", "is missing")

        if "path" not in adict:
            invalid_req.add_error("path", "is missing")

        if invalid_req.has_errors():
            return invalid_req

        return cls(
            data_source_id=adict.get("data_source_id"),
            path=adict.get("path"),
            ui_recipe=adict.get("ui_recipe"),
            attribute=adict.get("attribute"),
        )


class GetDocumentByPathUseCase(uc.UseCase):
    def __init__(self, repository_provider=get_repository):
        self.repository_provider = repository_provider
        self.document_service = DocumentService(repository_provider=self.repository_provider)

    def process_request(self, request_object: GetDocumentByPathRequestObject):
        data_source_id: str = request_object.data_source_id
        root_doc = get_document_by_ref(f"{data_source_id}/{request_object.path}")
        document_id = root_doc.uid
        attribute: str = request_object.attribute

        document = self.document_service.get_by_uid(data_source_id=data_source_id, document_uid=document_id)

        if attribute:
            document = document.get_by_path(attribute.split("."))

        blueprint = document.blueprint

        children = []
        dtos = []
        self.add_children_types(children, dtos, blueprint)

        return res.ResponseSuccess(
            {"blueprint": blueprint.to_dict_raw(), "document": document.to_dict(), "children": children, "dtos": dtos}
        )

    # TODO: Should this be handled be Node functions?
    # todo control recursive iterations iterations, decided by plugin?
    def add_children_types(self, children, dtos, blueprint):
        for attribute in blueprint.attributes:
            attribute_type = attribute.attribute_type
            self.add_dtos(dtos, attribute)
            if attribute_type not in PRIMITIVES:
                # prevent infinite recursion.
                child_blueprint_name = attribute_type.split("/")[-1]
                type_in_children = next((x for x in children if x["name"] == child_blueprint_name), None)
                if not type_in_children:
                    child_blueprint = self.document_service.blueprint_provider.get_blueprint(attribute_type)
                    if not isinstance(child_blueprint, (dict, type(None))):
                        children.append(child_blueprint.to_dict())
                        self.add_children_types(children, dtos, child_blueprint)

    # TODO: Should this be handled be Node functions?
    def add_dtos(self, dtos, attribute: BlueprintAttribute):
        if attribute.enum_type and len(attribute.enum_type) > 0:
            try:
                enum_blueprint: DTO = get_document_by_ref(attribute.enum_type)
                dtos.append(enum_blueprint.to_dict())
            except AttributeError as error:
                logger.exception(error)
                print(f"failed to append enumType {attribute}")
            except Exception as error:
                logger.exception(error)
                print(f"failed to append enumType {attribute}")