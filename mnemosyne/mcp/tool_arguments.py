import json
from typing import Any


def _matches_declared_type(value: object, declared: str) -> bool:
    if declared == "null":
        return value is None
    if declared == "boolean":
        return type(value) is bool
    if declared == "integer":
        return type(value) is int or (
            type(value) is float and value.is_integer()
        )
    if declared == "number":
        return type(value) in {int, float}
    if declared == "string":
        return isinstance(value, str)
    if declared == "array":
        return isinstance(value, list)
    if declared == "object":
        return isinstance(value, dict)
    return False


def _same_json_type(left: object, right: object) -> bool:
    if type(left) is bool or type(right) is bool:
        return type(left) is type(right)
    if type(left) in {int, float} and type(right) in {int, float}:
        return True
    return type(left) is type(right)


def _schema_permits_value_type(schema: dict[str, Any], value: object) -> bool:
    declared = schema.get("type")
    if isinstance(declared, str):
        if not _matches_declared_type(value, declared):
            return False
    elif isinstance(declared, list):
        if not any(
            isinstance(item, str) and _matches_declared_type(value, item)
            for item in declared
        ):
            return False

    if "const" in schema and not _same_json_type(value, schema["const"]):
        return False

    for keyword in ("oneOf", "anyOf"):
        branches = schema.get(keyword)
        if isinstance(branches, list) and not any(
            isinstance(branch, dict)
            and _schema_permits_value_type(branch, value)
            for branch in branches
        ):
            return False
    return True


def _branch_matches_object(branch: dict[str, Any], value: dict[str, Any]) -> bool:
    properties = branch.get("properties")
    if not isinstance(properties, dict):
        return True
    for name, property_schema in properties.items():
        if (
            isinstance(property_schema, dict)
            and "const" in property_schema
            and name in value
            and (
                not _same_json_type(value[name], property_schema["const"])
                or value[name] != property_schema["const"]
            )
        ):
            return False
    return True


def _property_schemas(
    schema: dict[str, Any],
    value: dict[str, Any],
    name: str,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    properties = schema.get("properties")
    if isinstance(properties, dict):
        property_schema = properties.get(name)
        if isinstance(property_schema, dict):
            matches.append(property_schema)

    for keyword in ("oneOf", "anyOf"):
        branches = schema.get(keyword)
        if not isinstance(branches, list):
            continue
        applicable = [
            branch
            for branch in branches
            if isinstance(branch, dict) and _branch_matches_object(branch, value)
        ]
        for branch in applicable:
            matches.extend(_property_schemas(branch, value, name))
    return matches


def _normalize(value: Any, schema: dict[str, Any]) -> Any:
    if isinstance(value, str) and not _schema_permits_value_type(schema, value):
        try:
            decoded = json.loads(value)
        except (json.JSONDecodeError, RecursionError, TypeError, ValueError):
            return value
        if not _schema_permits_value_type(schema, decoded):
            return value
        return decoded

    if isinstance(value, dict):
        normalized = dict(value)
        for name, item in value.items():
            schemas = _property_schemas(schema, value, name)
            if not schemas:
                continue
            property_schema = (
                schemas[0] if len(schemas) == 1 else {"anyOf": schemas}
            )
            normalized[name] = _normalize(item, property_schema)
        return normalized

    if isinstance(value, list):
        items = schema.get("items")
        if isinstance(items, dict):
            return [_normalize(item, items) for item in value]
    return value


def normalize_tool_arguments(
    arguments: dict[str, Any],
    input_schema: dict[str, Any],
) -> dict[str, Any]:
    """Decode one stringified JSON layer where a Tool schema requires it."""

    return _normalize(arguments, input_schema)
