from api.core.serializers.dto_json_serializer import DTOSerializer

from api.core.use_case.update_document_use_case import UpdateDocumentRequestObject, UpdateDocumentUseCase

from api.core.use_case.get_document_by_path_use_case import GetDocumentByPathUseCase, GetDocumentByPathRequestObject
from api.core.use_case.get_document_use_case import GetDocumentUseCase, GetDocumentRequestObject
from flask import Response, request
from controllers.status_codes import STATUS_CODES
import json


def get_by_id(data_source_id, document_id):
    ui_recipe = request.args.get("ui_recipe")
    attribute = request.args.get("attribute")
    use_case = GetDocumentUseCase()
    request_object = GetDocumentRequestObject.from_dict(
        {"data_source_id": data_source_id, "document_id": document_id, "ui_recipe": ui_recipe, "attribute": attribute}
    )
    response = use_case.execute(request_object)
    return Response(json.dumps(response.value), mimetype="application/json", status=STATUS_CODES[response.type])


def get_by_path(data_source_id):
    document_path = request.args.get("path")
    ui_recipe = request.args.get("ui_recipe")
    attribute = request.args.get("attribute")
    use_case = GetDocumentByPathUseCase()
    request_object = GetDocumentByPathRequestObject.from_dict(
        {"data_source_id": data_source_id, "path": document_path, "ui_recipe": ui_recipe, "attribute": attribute}
    )
    response = use_case.execute(request_object)
    return Response(json.dumps(response.value), mimetype="application/json", status=STATUS_CODES[response.type])


def update(data_source_id, document_id, body):
    # if connexion.request.is_json:
    #    calculation_body = CalculationBody.from_dict(connexion.request.get_json())

    data = request.get_json()
    attribute = request.args.get("attribute")
    request_object = UpdateDocumentRequestObject.from_dict(
        {"data_source_id": data_source_id, "data": data, "document_id": document_id, "attribute": attribute}
    )
    update_use_case = UpdateDocumentUseCase()
    response = update_use_case.execute(request_object)
    return Response(
        json.dumps(response.value, cls=DTOSerializer), mimetype="application/json", status=STATUS_CODES[response.type]
    )