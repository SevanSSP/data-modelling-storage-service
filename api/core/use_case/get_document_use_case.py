from core.domain.dto import DTO
from core.domain.template import Template
from core.repository.mongo.document_repository import DocumentRepository
from core.repository.repository_exceptions import EntityNotFoundException
from core.shared import request_object as req
from core.shared import response_object as res
from core.shared import use_case as uc
from core.use_case.utils.get_template import get_blueprint
from utils.form_to_schema import form_to_schema2
from utils.form_to_ui_schema import form_to_ui_schema


class GetDocumentRequestObject(req.ValidRequestObject):
    def __init__(self, document_id):
        self.document_id = document_id

    @classmethod
    def from_dict(cls, adict):
        invalid_req = req.InvalidRequestObject()

        if "document_id" not in adict:
            invalid_req.add_error("document_id", "is missing")

        if invalid_req.has_errors():
            return invalid_req

        return cls(document_id=adict.get("document_id"))


class GetDocumentUseCase(uc.UseCase):
    def __init__(self, document_repository: DocumentRepository, get_repository):
        self.document_repository = document_repository
        self.get_repository = get_repository

    def process_request(self, request_object: GetDocumentRequestObject):
        document_id = request_object.document_id
        dto: DTO = self.document_repository.get(document_id)
        if not dto:
            raise EntityNotFoundException(uid=document_id)

        # todo use dto_repository
        blueprint = get_blueprint(dto.type)
        data = blueprint.to_dict()

        # @todo move to template class, should have a custom template ReactJsonFormTemplate which translate our
        #  template to something react json schema understands.
        del data["type"]

        template = Template(
            schema=form_to_schema2(data), ui_recipes=form_to_ui_schema(blueprint), uiSchema={}, view=None
        )

        data = {"template": template.to_dict(), "document": dto.data}

        return res.ResponseSuccess(data)
