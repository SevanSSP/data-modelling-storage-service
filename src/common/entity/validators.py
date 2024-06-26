from collections.abc import Callable
from typing import Any, Literal

from common.exceptions import ValidationException
from domain_classes.blueprint import Blueprint
from domain_classes.blueprint_attribute import BlueprintAttribute
from enums import SIMOS, BuiltinDataTypes


def is_blueprint_instance_of(
    minimum_blueprint_type: str,
    blueprint_type: str,
    get_blueprint: Callable[..., Blueprint],
) -> bool:
    """Takes in a blueprint and checks if it's an instance of a minimum blueprint

    Args:
        minimum_blueprint_type: Blueprint to validate against
        blueprint_type: Blueprint to validate

    Returns:
        bool:
            Returns true if:
                the minimum blueprint has the generic "object" type, since all blueprints are objects
                the blueprint has the same type as the minimum blueprint
                the blueprint extends a blueprint that fulfills one of these three rules
            Otherwise it returns false.
    """
    if minimum_blueprint_type == BuiltinDataTypes.OBJECT.value:
        return True
    if minimum_blueprint_type == blueprint_type:
        return True
    for inherited_type in get_blueprint(blueprint_type).extends:
        if is_blueprint_instance_of(minimum_blueprint_type, inherited_type, get_blueprint):
            return True
    return False


def _validate_primitive_attribute(
    attribute: BlueprintAttribute, value: bool | int | float | str, key: str, get_blueprint: Callable[..., Blueprint]
):
    if attribute.attribute_type == BuiltinDataTypes.ANY.value:
        return  # If type is "any", no need to validate further
    python_type = BuiltinDataTypes(attribute.attribute_type).to_py_type()
    if attribute.enum_type:
        enum_entity = get_blueprint(attribute.enum_type).entity
        if value not in enum_entity["values"]:
            raise ValidationException(
                f"Attribute '{attribute.name}' is invalid. '{value}' is not a member of the enum '{attribute.enum_type}'. Valid values are {enum_entity['values']}",
                debug=_get_debug_message(key),
                data=attribute.to_dict(),
            )
    if attribute.attribute_type == "number" and isinstance(value, int):  # float is considered a superset containing int
        return
    if not python_type or not isinstance(value, python_type):
        raise ValidationException(
            f"Attribute '{attribute.name}' should be type '{python_type.__name__}'. Got '{type(value).__name__}'. Value: {value}",
            debug=_get_debug_message(key),
            data=attribute.to_dict(),
        )


def validate_entity_against_self(entity: dict | list, get_blueprint: Callable[..., Blueprint], key: str = "^") -> None:
    """Takes a complex entity (dict) or a list of entities and validates them against their own type.

    Args:
        key: Dotted path to the location of the current entity.

    Raises:
        Will raise a detailed "ValidationException" if the entity is invalid
    """
    if isinstance(entity, list):
        # TODO: Check that dimensions is correct
        for i, item in enumerate(entity):
            validate_entity_against_self(item, get_blueprint, key=f"{key}.{i}")
        return
    if not entity.get("type"):
        raise ValidationException(
            "Every entity must have a 'type' attribute", debug=_get_debug_message(key), data=entity
        )
    _validate_entity(entity, get_blueprint, get_blueprint(entity["type"]), "exact", key)


def validate_entity(
    entity: dict | list,
    get_blueprint: Callable[..., Blueprint],
    blueprint: Blueprint,
    implementation_mode: Literal["extend", "minimum", "exact"],
    key: str = "^",
) -> None:
    """Takes a complex entity (dict) or a list of entities and validates them against an arbitrary blueprint.

    Args:
        blueprint: Blueprint to check the entity against
        key: Dotted path to the location of the current entity.
        implementation_mode:
            extend: validate that the entity implements its own type and that this type extends the blueprint
            minimum: validate that the entity has all the attributes defined in the blueprint

    Raises:
        Will raise a detailed "ValidationException" if the entity is invalid
    """
    if isinstance(entity, list):
        # TODO: Check that dimensions is correct
        for i, item in enumerate(entity):
            _validate_entity(item, get_blueprint, blueprint, implementation_mode, f"{key}.{i}")
        return
    _validate_entity(entity, get_blueprint, blueprint, implementation_mode, key)


def _validate_entity(
    entity: dict,
    get_blueprint: Callable[..., Blueprint],
    blueprint: Blueprint,
    implementation_mode: Literal["exact", "extend", "minimum"],
    key: str,
) -> None:
    if not entity.get("type"):
        raise ValidationException(
            'Entity is missing required attribute "type"',
            debug=_get_debug_message(key),
            data=entity,
        )

    if implementation_mode == "extend":
        if entity["type"] != SIMOS.REFERENCE.value:
            if not is_blueprint_instance_of(blueprint.path, entity["type"], get_blueprint):
                raise ValidationException(
                    f"Entity should be of type '{blueprint.path}' (or extending from it). Got '{entity['type']}'",
                    debug=_get_debug_message(key),
                    data=entity,
                )
        implementation_mode = "exact"
        blueprint = get_blueprint(entity["type"])

    if implementation_mode == "exact":
        if keys_not_in_blueprint := [
            key for key in entity.keys() if key not in [*blueprint.get_attribute_names(), "_id"]
        ]:
            raise ValidationException(
                f"Attributes '{keys_not_in_blueprint}' are not specified in the blueprint '{blueprint.path}'",
                debug=_get_debug_message(key),
                data=entity,
            )
        if not blueprint.path == entity["type"]:
            raise ValidationException(
                f"Entity should be of type '{blueprint.path}'. Got '{entity['type']}'",
                debug=_get_debug_message(key),
                data=entity,
            )

    for attributeDefinition in blueprint.get_required_attributes():
        if entity.get(attributeDefinition.name, None) is None:
            raise ValidationException(
                f"Missing required attribute '{attributeDefinition.name}'", debug=_get_debug_message(key), data=entity
            )

    for attributeDefinition in [blueprint.get_attribute_by_name(key) for key in entity.keys()]:
        if attributeDefinition is None:
            continue
        elif attributeDefinition.is_array:
            _validate_list(
                entity[attributeDefinition.name],
                attributeDefinition,
                get_blueprint,
                f"{key}.{attributeDefinition.name}",
                len(attributeDefinition.dimensions.dimensions) if attributeDefinition.dimensions else 0,
                implementation_mode,
            )
        elif attributeDefinition.attribute_type == "any" and attributeDefinition.name == "default":
            default_attribute_definition = BlueprintAttribute(
                name=attributeDefinition.name,
                attribute_type=entity["attributeType"],
                dimensions=entity.get("dimensions", None),
            )
            if default_attribute_definition.is_array:
                _validate_list(
                    entity["default"],
                    default_attribute_definition,
                    get_blueprint,
                    f"{key}.{default_attribute_definition.name}",
                    len(default_attribute_definition.dimensions.dimensions),
                    "extend",
                )
            elif default_attribute_definition.is_primitive:
                try:
                    _validate_primitive_attribute(
                        default_attribute_definition,
                        entity["default"],
                        f"{key}.{default_attribute_definition.name}",
                        get_blueprint,
                    )
                except ValidationException as ex:
                    ex.data = entity
                    raise ex
            else:
                _validate_complex_attribute(
                    default_attribute_definition,
                    entity["default"],
                    get_blueprint,
                    f"{key}.{default_attribute_definition.name}",
                    "extend",
                )
        elif attributeDefinition.is_primitive:
            _validate_primitive_attribute(
                attributeDefinition,
                entity[attributeDefinition.name],
                f"{key}.{attributeDefinition.name}",
                get_blueprint,
            )
        else:
            _validate_complex_attribute(
                attributeDefinition,
                entity[attributeDefinition.name],
                get_blueprint,
                f"{key}.{attributeDefinition.name}",
                implementation_mode,
            )


def _validate_complex_attribute(
    attributeDefinition: BlueprintAttribute,
    attribute: Any,
    get_blueprint: Callable[..., Blueprint],
    key: str,
    implementation_mode: Literal["exact", "extend", "minimum"],
):
    if not isinstance(attribute, dict):
        raise ValidationException(
            f"'{attributeDefinition.name}' should be a dict, got {attribute}",
            debug=_get_debug_message(key),
            data=attribute.to_dict(),
        )
    if not attribute or attributeDefinition.attribute_type == BuiltinDataTypes.BINARY.value:
        return
    if attributeDefinition.attribute_type == BuiltinDataTypes.OBJECT.value:
        validate_entity_against_self(entity=attribute, get_blueprint=get_blueprint, key=key)
        return

    if attributeDefinition.ensure_uid and not attribute.get("_id"):
        raise ValidationException(
            f"The attribute '{attributeDefinition.name}', requires "
            + "the entity to have a UUID. Make sure the entity has a valid UUIDv4 at the key '_id'",
            debug=_get_debug_message(key),
            data=attribute,
        )
    _validate_entity(
        attribute,
        get_blueprint,
        get_blueprint(attributeDefinition.attribute_type),
        "minimum" if implementation_mode == "minimum" else "extend",
        key,
    )


def _get_debug_message(key: str):
    return f"Location: Entity in key '{key}'"


def _validate_list(
    attribute: Any,
    attributeDefinition: BlueprintAttribute,
    get_blueprint: Callable[..., Blueprint],
    key: str,
    dimensions: int,
    implementation_mode: Literal["exact", "extend", "minimum"],
):
    if not isinstance(attribute, list):
        raise ValidationException(
            f"'{attributeDefinition.name}' should be a list", debug=_get_debug_message(key), data=attribute.to_dict()
        )
    for i, item in enumerate(attribute):
        if dimensions > 1:
            _validate_list(
                item,
                attributeDefinition,
                get_blueprint,
                f"{key}.{i}",
                dimensions - 1,
                implementation_mode,
            )
        elif attributeDefinition.is_primitive:
            _validate_primitive_attribute(attributeDefinition, item, f"{key}.{i}", get_blueprint)
        else:
            _validate_complex_attribute(
                attributeDefinition,
                item,
                get_blueprint,
                f"{key}.{i}",
                implementation_mode,
            )
