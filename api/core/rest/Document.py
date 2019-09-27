import json
from flask import Blueprint, Response, request
from classes.data_source import DataSource
from core.use_case.generate_json_schema_use_case import GenerateJsonSchemaUseCase, GenerateJsonSchemaRequestObject
from utils.logging import logger
from core.domain.document import Document
from core.use_case.get_document_with_template_use_case import (
    GetDocumentWithTemplateUseCase,
    GetDocumentWithTemplateRequestObject,
)
from core.shared import response_object as res
from core.use_case.add_document_use_case import AddDocumentUseCase
from core.repository.repository_factory import get_repository, RepositoryType
from core.use_case.update_document_use_case import UpdateDocumentUseCase

blueprint = Blueprint("document", __name__)

STATUS_CODES = {
    res.ResponseSuccess.SUCCESS: 200,
    res.ResponseFailure.RESOURCE_ERROR: 404,
    res.ResponseFailure.PARAMETERS_ERROR: 400,
    res.ResponseFailure.SYSTEM_ERROR: 500,
}


@blueprint.route("/api/v2/json-schema/<path:template_ref>", methods=["GET"])
def get_json_schema(template_ref: str):
    logger.info(f"Getting json-schema '{template_ref}'")
    use_case = GenerateJsonSchemaUseCase(get_repository)
    request_object = GenerateJsonSchemaRequestObject.from_dict({"templateRef": template_ref})
    response = use_case.execute(request_object)
    return Response(json.dumps(response.value), mimetype="application/json", status=STATUS_CODES[response.type])


@blueprint.route("/api/v2/documents/<string:data_source_id>/<path:document_id>", methods=["GET"])
def get(data_source_id: str, document_id: str):
    logger.info(f"Getting document '{document_id}' from data source '{data_source_id}'")

    db = DataSource(id=data_source_id)

    document_repository = get_repository(RepositoryType.BlueprintRepository, db)

    use_case = GetDocumentWithTemplateUseCase(document_repository, get_repository)
    request_object = GetDocumentWithTemplateRequestObject.from_dict({"document_id": document_id})
    response = use_case.execute(request_object)
    return Response(json.dumps(response.value), mimetype="application/json", status=STATUS_CODES[response.type])


@blueprint.route("/api/v2/documents/<string:data_source_id>", methods=["POST"])
def post(data_source_id: str):
    logger.info(f"Creating document in data source '{data_source_id}'")

    data = request.get_json()

    db = DataSource(id=data_source_id)

    document_repository = get_repository(RepositoryType.DocumentRepository, db)

    document = Document.from_dict(data)

    add_use_case = AddDocumentUseCase(document_repository)
    add_use_case.execute(document)

    use_case = GetDocumentWithTemplateUseCase(document_repository, get_repository)
    request_object = GetDocumentWithTemplateRequestObject.from_dict({"document_id": document.uid})
    response = use_case.execute(request_object)
    return Response(json.dumps(response.value), mimetype="application/json", status=STATUS_CODES[response.type])


@blueprint.route("/api/v2/documents/<string:data_source_id>/<string:document_id>", methods=["PUT"])
@blueprint.route(
    "/api/v2/documents/<string:data_source_id>/<string:document_id>/<path:attribute_path>", methods=["PUT"]
)
def put(data_source_id: str, document_id: str, attribute_path: str = None):
    logger.info(f"Updating document '{document_id}' in data source '{data_source_id}'")

    data = request.get_json()

    db = DataSource(id=data_source_id)

    document_repository = get_repository(RepositoryType.BlueprintRepository, db)

    add_use_case = UpdateDocumentUseCase(document_repository)
    add_use_case.execute(document_id, data, attribute_path)

    use_case = GetDocumentWithTemplateUseCase(document_repository, get_repository)
    request_object = GetDocumentWithTemplateRequestObject.from_dict({"document_id": document_id})
    response = use_case.execute(request_object)
    return Response(json.dumps(response.value), mimetype="application/json", status=STATUS_CODES[response.type])
