# pylint: disable=redefined-outer-name

import pytest
from models_library.osparc_variable_identifier import (
    OsparcVariableIdentifier,
    UnresolvedOsparcVariableIdentifierError,
    raise_if_unresolved,
)
from pydantic import ValidationError, parse_obj_as

VALID_IDENTIFIERS: list[str] = [
    "$OSPARC_VARIABLE_One121_",
    "$OSPARC_VARIABLE_121Asdasd_",
    "$OSPARC_VARIABLE_1212aaS_",
    "${OSPARC_VARIABLE_ONE}",
    "${OSPARC_VARIABLE_1}",
    "${OSPARC_VARIABLE_1:-default_value}",
    "${OSPARC_VARIABLE_1:-{}}",
    "${OSPARC_VARIABLE_1:-}",
]

INVALID_IDENTIFIERS: list[str] = [
    "${OSPARC_VARIABLE_1:default_value}",
    "${OSPARC_VARIABLE_1:{}}",
    "${OSPARC_VARIABLE_1:}",
    "${OSPARC_VARIABLE_1-default_value}",
    "${OSPARC_VARIABLE_1-{}}",
    "${OSPARC_VARIABLE_1-}",
]


@pytest.fixture(params=VALID_IDENTIFIERS)
def osparc_variable_identifier_str(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture
def identifier(
    osparc_variable_identifier_str: str,
) -> OsparcVariableIdentifier:
    return parse_obj_as(OsparcVariableIdentifier, osparc_variable_identifier_str)


@pytest.mark.parametrize("invalid_var_name", INVALID_IDENTIFIERS)
def test_osparc_variable_identifier_does_not_validate(invalid_var_name: str):
    with pytest.raises(ValidationError):
        parse_obj_as(OsparcVariableIdentifier, invalid_var_name)


def test_raise_if_unresolved(identifier: OsparcVariableIdentifier):
    def example_func(par: OsparcVariableIdentifier | int) -> None:
        _ = 12 + raise_if_unresolved(par)

    example_func(1)

    with pytest.raises(UnresolvedOsparcVariableIdentifierError):
        example_func(identifier)


@pytest.mark.parametrize(
    "str_identifier, expected_osparc_variable_name, expected_default_value",
    list(
        zip(
            VALID_IDENTIFIERS,
            [
                "OSPARC_VARIABLE_One121_",
                "OSPARC_VARIABLE_121Asdasd_",
                "OSPARC_VARIABLE_1212aaS_",
                "OSPARC_VARIABLE_ONE",
                "OSPARC_VARIABLE_1",
                "OSPARC_VARIABLE_1",
                "OSPARC_VARIABLE_1",
                "OSPARC_VARIABLE_1",
            ],
            [
                None,
                None,
                None,
                None,
                None,
                "default_value",
                "{}",
                "",
            ],
            strict=True,
        )
    ),
)
def test_osparc_variable_name_and_default_value(
    str_identifier: str,
    expected_osparc_variable_name: str,
    expected_default_value: str | None,
):
    osparc_variable_identifer = parse_obj_as(OsparcVariableIdentifier, str_identifier)
    assert osparc_variable_identifer.name == expected_osparc_variable_name
    assert osparc_variable_identifer.default_value == expected_default_value
