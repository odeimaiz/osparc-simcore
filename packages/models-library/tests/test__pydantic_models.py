"""This test suite does not intend to re-test pydantic but rather
check some "corner cases" or critical setups with pydantic model such that:

- we can ensure a given behaviour is preserved through updates
- document/clarify some concept

"""

from typing import Any, Literal, Union, get_args, get_origin

import pytest
from common_library.json_serialization import json_dumps
from models_library.projects_nodes import InputTypes, OutputTypes
from models_library.projects_nodes_io import SimCoreFileLink
from models_library.utils.change_case import snake_to_camel
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError
from pydantic.types import Json
from pydantic.version import version_short

# NOTE: pydantic at a glance (just a few key features):
#
# structured data  -->| (parse+validate) --> [ Model.fields ] --> (export)                       |--> structured data
# - no guarantees         - map (alias)       - accessors        - filter (include/exclude ...)       - w/ guarantees
#                         - ...               - doc              - map (by_alias, copy&udpate )
#                                                                - format (json, dict)
#
# NOTE: think of the direction of data in a pydantic model. It defines how the field contraints are defined! The
#    model does not necessarily can be used in the opposite direction. e.g. cannot always use the same model
#    to read from a database and to write in it.
#


def test_json_type():
    # Json data type first load a raw JSON string and parses it into a nested dict
    # SEE https://pydantic-docs.helpmanual.io/usage/types/#json-type

    class ArgumentAnnotation(BaseModel):
        name: str
        data_schema: Json

    # notice that this is a raw string!
    jsonschema_of_x = json_dumps(
        {**TypeAdapter(list[int]).json_schema(), "title": "schema[x]"}
    )
    assert isinstance(jsonschema_of_x, str)

    x_annotation = ArgumentAnnotation(name="x", data_schema=jsonschema_of_x)

    # x_schema was parsed as a string into a nested dict
    assert x_annotation.data_schema != jsonschema_of_x
    assert x_annotation.data_schema == {
        "title": "schema[x]",
        "type": "array",
        "items": {"type": "integer"},
    }

    assert x_annotation.model_dump() == {
        "name": "x",
        "data_schema": {
            "title": "schema[x]",
            "type": "array",
            "items": {"type": "integer"},
        },
    }

    # Notice how this model is not "reversable", i.e. exported outputs
    # cannot be used as inputs again
    #
    # the constructor would expect a raw string but we produced a nested dict
    with pytest.raises(ValidationError) as exc_info:
        ArgumentAnnotation(**x_annotation.model_dump())

    assert exc_info.value.errors()[0] == {
        "input": {"items": {"type": "integer"}, "title": "schema[x]", "type": "array"},
        "loc": ("data_schema",),
        "msg": "JSON input should be string, bytes or bytearray",
        "type": "json_type",
        "url": f"https://errors.pydantic.dev/{version_short()}/v/json_type",
    }

    with pytest.raises(ValidationError) as exc_info:
        ArgumentAnnotation(name="foo", data_schema="invalid-json")

    assert exc_info.value.errors()[0] == {
        "ctx": {"error": "expected value at line 1 column 1"},
        "input": "invalid-json",
        "loc": ("data_schema",),
        "msg": "Invalid JSON: expected value at line 1 column 1",
        "type": "json_invalid",
        "url": f"https://errors.pydantic.dev/{version_short()}/v/json_invalid",
    }


def test_union_types_coercion():
    # SEE https://pydantic-docs.helpmanual.io/usage/types/#unions
    class Func(BaseModel):
        input: InputTypes = Field(union_mode="left_to_right")
        output: OutputTypes = Field(union_mode="left_to_right")

    assert get_origin(InputTypes) is Union
    assert get_origin(OutputTypes) is Union
    #
    # pydantic will attempt to 'match' any of the types defined under Union and will use the first one that matches
    # NOTE: it is recommended that, when defining Union annotations, the most specific type is included first and followed by less specific types.
    #

    assert Func.model_json_schema()["properties"]["input"] == {
        "title": "Input",
        "anyOf": [
            {"type": "boolean"},
            {"type": "integer"},
            {"type": "number"},
            {
                "contentMediaType": "application/json",
                "contentSchema": {},
                "type": "string",
            },
            {"type": "string"},
            {"$ref": "#/$defs/PortLink"},
            {"$ref": "#/$defs/SimCoreFileLink"},
            {"$ref": "#/$defs/DatCoreFileLink"},
            {"$ref": "#/$defs/DownloadLink"},
            {"type": "array", "items": {}},
            {"type": "object", "additionalProperties": True},
        ],
    }

    # integers ------------------------
    model = Func.model_validate({"input": "0", "output": 1})
    print(model.model_dump_json(indent=1))

    assert model.input == 0
    assert model.output == 1

    # numbers and bool ------------------------
    model = Func.model_validate({"input": "0.5", "output": "false"})
    print(model.model_dump_json(indent=1))

    assert model.input == 0.5
    assert model.output is False

    # (undefined) json string vs string ------------------------
    model = Func.model_validate(
        {
            "input": '{"w": 42, "z": false}',  # NOTE: this is a raw json string
            "output": "some/path/or/string",
        }
    )
    print(model.model_dump_json(indent=1))

    assert model.input == {"w": 42, "z": False}
    assert model.output == "some/path/or/string"

    # (undefined) json string vs SimCoreFileLink.model_dump() ------------
    MINIMAL = 2  # <--- index of the example with the minimum required fields
    assert SimCoreFileLink in get_args(OutputTypes)
    example = SimCoreFileLink.model_validate(
        SimCoreFileLink.model_json_schema()["examples"][MINIMAL]
    )
    model = Func.model_validate(
        {
            "input": '{"w": 42, "z": false}',
            "output": example.model_dump(
                exclude_unset=True
            ),  # NOTE: this is NOT a raw json string
        }
    )
    print(model.model_dump_json(indent=1))
    assert model.input == {"w": 42, "z": False}
    assert model.output == example
    assert isinstance(model.output, SimCoreFileLink)

    # json array and objects
    model = Func.model_validate(
        {"input": {"w": 42, "z": False}, "output": [1, 2, 3, None]}
    )
    print(model.model_dump_json(indent=1))
    assert model.input == {"w": 42, "z": False}
    assert model.output == [1, 2, 3, None]


def test_nullable_fields_from_pydantic_v1():
    # Tests issue found during migration. Pydantic v1 would default to None all nullable fields when they were not **explicitly** set with `...` as required
    # SEE https://github.com/ITISFoundation/osparc-simcore/pull/6751
    class MyModel(BaseModel):
        # pydanticv1 would add a default to fields set as nullable
        nullable_required: (
            str | None
        )  # <--- This was default to =None in pydantic 1 !!!
        nullable_required_with_hyphen: str | None = Field(default=...)
        nullable_optional: str | None = None

        # but with non-nullable "required" worked both ways
        non_nullable_required: int
        non_nullable_required_with_hyphen: int = Field(default=...)
        non_nullable_optional: int = 42

    data: dict[str, Any] = {
        "nullable_required_with_hyphen": "foo",
        "non_nullable_required_with_hyphen": 1,
        "non_nullable_required": 2,
    }

    with pytest.raises(ValidationError) as err_info:
        MyModel.model_validate(data)

    assert err_info.value.error_count() == 1
    error = err_info.value.errors()[0]
    assert error["type"] == "missing"
    assert error["loc"] == ("nullable_required",)

    data["nullable_required"] = None
    model = MyModel.model_validate(data)
    assert model.model_dump(exclude_unset=True) == data


# BELOW some tests related to deprecated `populate_by_name` in pydantic v2.11+ !!
#
# https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.populate_by_name
#
# `populate_by_name` usage is not recommended in v2.11+ and will be deprecated in v3. Instead, you should use the validate_by_name configuration setting.
# When validate_by_name=True and validate_by_alias=True, this is strictly equivalent to the previous behavior of populate_by_name=True.
# In v2.11, we also introduced a validate_by_alias setting that introduces more fine grained control for validation behavior.
# Here's how you might go about using the new settings to achieve the same behavior:
#


@pytest.mark.parametrize("extra", ["ignore", "allow", "forbid"])
@pytest.mark.parametrize(
    "validate_by_alias, validate_by_name",
    [
        # NOTE: (False, False) is not allowed: at least one has to be True!
        # SEE https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.validate_by_alias
        (False, True),
        (True, False),
        (True, True),
    ],
)
def test_model_config_validate_by_alias_and_name(
    validate_by_alias: bool,
    validate_by_name: bool,
    extra: Literal["ignore", "allow", "forbid"],
):
    class TestModel(BaseModel):
        snake_case: str | None = None

        model_config = ConfigDict(
            validate_by_alias=validate_by_alias,
            validate_by_name=validate_by_name,
            extra=extra,
            alias_generator=snake_to_camel,
        )

    assert TestModel.model_config.get("populate_by_name") is None
    assert TestModel.model_config.get("validate_by_alias") is validate_by_alias
    assert TestModel.model_config.get("validate_by_name") is validate_by_name
    assert TestModel.model_config.get("extra") == extra

    if validate_by_alias is False:

        if extra == "forbid":
            with pytest.raises(ValidationError):
                TestModel.model_validate({"snakeCase": "foo"})

        elif extra == "ignore":
            model = TestModel.model_validate({"snakeCase": "foo"})
            assert model.snake_case is None
            assert model.model_dump() == {"snake_case": None}

        elif extra == "allow":
            model = TestModel.model_validate({"snakeCase": "foo"})
            assert model.snake_case is None
            assert model.model_dump() == {"snake_case": None, "snakeCase": "foo"}

    else:
        assert TestModel.model_validate({"snakeCase": "foo"}).snake_case == "foo"

    if validate_by_name is False:
        if extra == "forbid":
            with pytest.raises(ValidationError):
                TestModel.model_validate({"snake_case": "foo"})

        elif extra == "ignore":
            model = TestModel.model_validate({"snake_case": "foo"})
            assert model.snake_case is None
            assert model.model_dump() == {"snake_case": None}

        elif extra == "allow":
            model = TestModel.model_validate({"snake_case": "foo"})
            assert model.snake_case is None
            assert model.model_dump() == {"snake_case": "foo"}
    else:
        assert TestModel.model_validate({"snake_case": "foo"}).snake_case == "foo"


@pytest.mark.parametrize("populate_by_name", [True, False])
def test_model_config_populate_by_name(populate_by_name: bool):
    # SEE https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.populate_by_name
    class TestModel(BaseModel):
        snake_case: str | None = None

        model_config = ConfigDict(
            populate_by_name=populate_by_name,
            extra="forbid",  # easier to check the effect of populate_by_name!
            alias_generator=snake_to_camel,
        )

    # checks how they are set
    assert TestModel.model_config.get("populate_by_name") is populate_by_name
    assert TestModel.model_config.get("extra") == "forbid"

    # NOTE how defaults work with populate_by_name!!
    assert TestModel.model_config.get("validate_by_name") == populate_by_name
    assert TestModel.model_config.get("validate_by_alias") is True  # Default

    # validate_by_alias BEHAVIUOR defaults to True
    TestModel.model_validate({"snakeCase": "foo"})

    if populate_by_name:
        assert TestModel.model_validate({"snake_case": "foo"}).snake_case == "foo"
    else:
        with pytest.raises(ValidationError):
            TestModel.model_validate({"snake_case": "foo"})
