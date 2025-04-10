import re
from typing import Annotated, Any, Literal, NamedTuple, TypeAlias, cast

from models_library.basic_types import IDStr
from models_library.licenses import VIP_DETAILS_EXAMPLE, FeaturesDict
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    TypeAdapter,
)
from pydantic.config import JsonDict

_max_str_adapter: TypeAdapter[str] = TypeAdapter(
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=1_000)]
)


def _clean_dict_data(data_dict):
    """
    Strips leading/trailing whitespace from all string values
    and removes keys whose stripped value is empty.
    """
    cleaned = {}
    for k, v in data_dict.items():
        if v is not None:
            if isinstance(v, str):
                v_stripped = v.strip()
                # Keep the key only if it's not empty after strip
                if v_stripped:
                    cleaned[k] = v_stripped
            else:
                # If it's not a string, just copy the value as is
                cleaned[k] = v
    return cleaned


def _feature_descriptor_to_dict(descriptor: str) -> dict[str, Any]:
    # NOTE: this is manually added in the server side so be more robust to errors
    descriptor = _max_str_adapter.validate_python(descriptor.strip("{}"))
    pattern = r"(\w{1,100}):\s*([^,]{1,100})"
    matches = re.findall(pattern, descriptor)
    return dict(matches)


class ItisVipData(BaseModel):
    # Designed to parse items from response from VIP-API
    id: Annotated[int, Field(alias="ID")]
    description: Annotated[str, Field(alias="Description")]
    thumbnail: Annotated[str, Field(alias="Thumbnail")]
    features: Annotated[
        FeaturesDict,
        BeforeValidator(_clean_dict_data),
        BeforeValidator(_feature_descriptor_to_dict),
        Field(alias="Features"),
    ]
    doi: Annotated[str | None, Field(alias="DOI")]
    license_key: Annotated[
        str,
        Field(
            alias="LicenseKey",
            description="NOTE: skips VIP w/o license key",
        ),
    ]
    license_version: Annotated[
        str,
        Field(
            alias="LicenseVersion",
            description="NOTE: skips VIP w/o license version",
        ),
    ]
    protection: Annotated[Literal["Code", "PayPal"], Field(alias="Protection")]
    available_from_url: Annotated[HttpUrl | None, Field(alias="AvailableFromURL")]

    @staticmethod
    def _update_json_schema_extra(schema: JsonDict) -> None:
        schema.update(
            {
                "examples": [
                    # complete
                    cast(JsonDict, VIP_DETAILS_EXAMPLE),
                    # minimal
                    {
                        "id": 1,
                        "description": "A detailed description of the VIP model",
                        "thumbnail": "https://example.com/thumbnail.jpg",
                        "features": {"date": "2013-02-01"},
                        "doi": "null",
                        "license_key": "ABC123XYZ",
                        "license_version": "1.0",
                        "protection": "Code",
                        "available_from_url": "null",
                    },
                ]
            }
        )

    model_config = ConfigDict(json_schema_extra=_update_json_schema_extra)


class ItisVipResourceData(BaseModel):
    category_id: IDStr
    category_display: str
    source: Annotated[
        ItisVipData, Field(description="Original published data in the api")
    ]
    terms_of_use_url: HttpUrl | None = None


CategoryID: TypeAlias = IDStr
CategoryDisplay: TypeAlias = str


class CategoryTuple(NamedTuple):
    url: HttpUrl
    id: CategoryID
    display: CategoryDisplay
