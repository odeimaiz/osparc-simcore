import datetime
from functools import cached_property
from typing import Annotated, Final, Self, cast

from aws_library.ec2 import EC2InstanceBootSpecific, EC2Tags
from fastapi import FastAPI
from models_library.basic_types import LogLevel, PortInt, VersionTag
from models_library.clusters import ClusterAuthentication
from models_library.docker import DockerLabelKey
from pydantic import (
    AliasChoices,
    AnyUrl,
    Field,
    NonNegativeInt,
    TypeAdapter,
    field_validator,
    model_validator,
)
from pydantic_settings import SettingsConfigDict
from servicelib.logging_utils import LogLevelInt
from servicelib.logging_utils_filtering import LoggerName, MessageSubstring
from settings_library.application import BaseApplicationSettings
from settings_library.base import BaseCustomSettings
from settings_library.docker_registry import RegistrySettings
from settings_library.ec2 import EC2Settings
from settings_library.rabbit import RabbitSettings
from settings_library.redis import RedisSettings
from settings_library.ssm import SSMSettings
from settings_library.tracing import TracingSettings
from settings_library.utils_logging import MixinLoggingSettings
from types_aiobotocore_ec2.literals import InstanceTypeType

from .._meta import API_VERSION, API_VTAG, APP_NAME

AUTOSCALING_ENV_PREFIX: Final[str] = "AUTOSCALING_"


class AutoscalingSSMSettings(SSMSettings): ...


class AutoscalingEC2Settings(EC2Settings):
    model_config = SettingsConfigDict(
        env_prefix=AUTOSCALING_ENV_PREFIX,
        json_schema_extra={
            "examples": [
                {
                    f"{AUTOSCALING_ENV_PREFIX}EC2_ACCESS_KEY_ID": "my_access_key_id",
                    f"{AUTOSCALING_ENV_PREFIX}EC2_ENDPOINT": "https://my_ec2_endpoint.com",
                    f"{AUTOSCALING_ENV_PREFIX}EC2_REGION_NAME": "us-east-1",
                    f"{AUTOSCALING_ENV_PREFIX}EC2_SECRET_ACCESS_KEY": "my_secret_access_key",
                }
            ],
        },
    )


class EC2InstancesSettings(BaseCustomSettings):
    EC2_INSTANCES_ALLOWED_TYPES: Annotated[
        dict[str, EC2InstanceBootSpecific],
        Field(
            description="Defines which EC2 instances are considered as candidates for new EC2 instance and their respective boot specific parameters"
            "NOTE: minimum length >0",
        ),
    ]

    EC2_INSTANCES_KEY_NAME: Annotated[
        str,
        Field(
            min_length=1,
            description="SSH key filename (without ext) to access the instance through SSH"
            " (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html),"
            "this is required to start a new EC2 instance",
        ),
    ]
    EC2_INSTANCES_MACHINES_BUFFER: Annotated[
        NonNegativeInt,
        Field(
            description="Constant reserve of drained ready machines for fast(er) usage,"
            "disabled when set to 0. Uses 1st machine defined in EC2_INSTANCES_ALLOWED_TYPES",
        ),
    ] = 0
    EC2_INSTANCES_MAX_INSTANCES: Annotated[
        int,
        Field(
            description="Defines the maximum number of instances the autoscaling app may create",
        ),
    ] = 10
    EC2_INSTANCES_MAX_START_TIME: Annotated[
        datetime.timedelta,
        Field(
            description="Usual time taken an EC2 instance with the given AMI takes to join the cluster "
            "(default to seconds, or see https://pydantic-docs.helpmanual.io/usage/types/#datetime-types for string formating)."
            "NOTE: be careful that this time should always be a factor larger than the real time, as EC2 instances"
            "that take longer than this time will be terminated as sometimes it happens that EC2 machine fail on start.",
        ),
    ] = datetime.timedelta(minutes=1)

    EC2_INSTANCES_NAME_PREFIX: Annotated[
        str,
        Field(
            min_length=1,
            description="prefix used to name the EC2 instances created by this instance of autoscaling",
        ),
    ] = "autoscaling"

    EC2_INSTANCES_SECURITY_GROUP_IDS: Annotated[
        list[str],
        Field(
            min_length=1,
            description="A security group acts as a virtual firewall for your EC2 instances to control incoming and outgoing traffic"
            " (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html), "
            " this is required to start a new EC2 instance",
        ),
    ]
    EC2_INSTANCES_SUBNET_ID: Annotated[
        str,
        Field(
            min_length=1,
            description="A subnet is a range of IP addresses in your VPC "
            " (https://docs.aws.amazon.com/vpc/latest/userguide/configure-subnets.html), "
            "this is required to start a new EC2 instance",
        ),
    ]
    EC2_INSTANCES_TIME_BEFORE_DRAINING: Annotated[
        datetime.timedelta,
        Field(
            description="Time after which an EC2 instance may be drained (10s<=T<=1 minutes, is automatically capped)"
            "(default to seconds, or see https://pydantic-docs.helpmanual.io/usage/types/#datetime-types for string formating)",
        ),
    ] = datetime.timedelta(seconds=20)

    EC2_INSTANCES_TIME_BEFORE_TERMINATION: Annotated[
        datetime.timedelta,
        Field(
            description="Time after which an EC2 instance may begin the termination process (0<=T<=59 minutes, is automatically capped)"
            "(default to seconds, or see https://pydantic-docs.helpmanual.io/usage/types/#datetime-types for string formating)",
        ),
    ] = datetime.timedelta(minutes=1)

    EC2_INSTANCES_TIME_BEFORE_FINAL_TERMINATION: Annotated[
        datetime.timedelta,
        Field(
            description="Time after which an EC2 instance is terminated after draining"
            "(default to seconds, or see https://pydantic-docs.helpmanual.io/usage/types/#datetime-types for string formating)",
        ),
    ] = datetime.timedelta(seconds=30)

    EC2_INSTANCES_CUSTOM_TAGS: Annotated[
        EC2Tags,
        Field(
            description="Allows to define tags that should be added to the created EC2 instance default tags. "
            "a tag must have a key and an optional value. see [https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Using_Tags.html]",
        ),
    ]
    EC2_INSTANCES_ATTACHED_IAM_PROFILE: Annotated[
        str,
        Field(
            description="ARN the EC2 instance should be attached to (example: arn:aws:iam::XXXXX:role/NAME), to disable pass an empty string",
        ),
    ]

    @field_validator("EC2_INSTANCES_TIME_BEFORE_DRAINING")
    @classmethod
    def _ensure_draining_delay_time_is_in_range(
        cls, value: datetime.timedelta
    ) -> datetime.timedelta:
        if value < datetime.timedelta(seconds=10):
            value = datetime.timedelta(seconds=10)
        elif value > datetime.timedelta(minutes=1):
            value = datetime.timedelta(minutes=1)
        return value

    @field_validator("EC2_INSTANCES_TIME_BEFORE_TERMINATION")
    @classmethod
    def _ensure_termination_delay_time_is_in_range(
        cls, value: datetime.timedelta
    ) -> datetime.timedelta:
        if value < datetime.timedelta(minutes=0):
            value = datetime.timedelta(minutes=0)
        elif value > datetime.timedelta(minutes=59):
            value = datetime.timedelta(minutes=59)
        return value

    @field_validator("EC2_INSTANCES_ALLOWED_TYPES")
    @classmethod
    def _check_valid_instance_names_and_not_empty(
        cls, value: dict[str, EC2InstanceBootSpecific]
    ) -> dict[str, EC2InstanceBootSpecific]:
        # NOTE: needed because of a flaw in BaseCustomSettings
        # issubclass raises TypeError if used on Aliases
        TypeAdapter(list[InstanceTypeType]).validate_python(list(value))

        if not value:
            # NOTE: Field( ... , min_items=...) cannot be used to contraint number of iterms in a dict
            msg = "At least one item expecte EC2_INSTANCES_ALLOWED_TYPES, got none"
            raise ValueError(msg)

        return value


class NodesMonitoringSettings(BaseCustomSettings):
    NODES_MONITORING_NODE_LABELS: Annotated[
        list[DockerLabelKey],
        Field(
            description="autoscaling will only monitor nodes with the given labels (if empty all nodes will be monitored), these labels will be added to the new created nodes by default",
        ),
    ]

    NODES_MONITORING_SERVICE_LABELS: Annotated[
        list[DockerLabelKey],
        Field(
            description="autoscaling will only monitor services with the given labels (if empty all services will be monitored)",
        ),
    ]

    NODES_MONITORING_NEW_NODES_LABELS: Annotated[
        list[DockerLabelKey],
        Field(
            description="autoscaling will add these labels to any new node it creates (additional to the ones in NODES_MONITORING_NODE_LABELS",
        ),
    ]


class DaskMonitoringSettings(BaseCustomSettings):
    DASK_MONITORING_URL: Annotated[
        AnyUrl, Field(description="the url to the dask-scheduler")
    ]
    DASK_SCHEDULER_AUTH: Annotated[
        ClusterAuthentication,
        Field(
            description="defines the authentication of the clusters created via clusters-keeper (can be None or TLS)",
        ),
    ]


class ApplicationSettings(BaseApplicationSettings, MixinLoggingSettings):
    # CODE STATICS ---------------------------------------------------------
    API_VERSION: str = API_VERSION
    APP_NAME: str = APP_NAME
    API_VTAG: VersionTag = API_VTAG

    # RUNTIME  -----------------------------------------------------------
    AUTOSCALING_DEBUG: Annotated[
        bool,
        Field(
            description="Debug mode",
            validation_alias=AliasChoices("AUTOSCALING_DEBUG", "DEBUG"),
        ),
    ] = False

    AUTOSCALING_REMOTE_DEBUG_PORT: PortInt = 3000

    AUTOSCALING_LOGLEVEL: Annotated[
        LogLevel,
        Field(
            LogLevel.INFO,
            validation_alias=AliasChoices(
                "AUTOSCALING_LOGLEVEL", "LOG_LEVEL", "LOGLEVEL"
            ),
        ),
    ]
    AUTOSCALING_LOG_FORMAT_LOCAL_DEV_ENABLED: Annotated[
        bool,
        Field(
            validation_alias=AliasChoices(
                "AUTOSCALING_LOG_FORMAT_LOCAL_DEV_ENABLED",
                "LOG_FORMAT_LOCAL_DEV_ENABLED",
            ),
            description="Enables local development log format. WARNING: make sure it is disabled if you want to have structured logs!",
        ),
    ] = False

    AUTOSCALING_LOG_FILTER_MAPPING: Annotated[
        dict[LoggerName, list[MessageSubstring]],
        Field(
            default_factory=dict,
            validation_alias=AliasChoices(
                "AUTOSCALING_LOG_FILTER_MAPPING", "LOG_FILTER_MAPPING"
            ),
            description="is a dictionary that maps specific loggers (such as 'uvicorn.access' or 'gunicorn.access') to a list of log message patterns that should be filtered out.",
        ),
    ]

    AUTOSCALING_EC2_ACCESS: Annotated[
        AutoscalingEC2Settings | None,
        Field(json_schema_extra={"auto_default_from_env": True}),
    ]

    AUTOSCALING_SSM_ACCESS: Annotated[
        AutoscalingSSMSettings | None,
        Field(json_schema_extra={"auto_default_from_env": True}),
    ]

    AUTOSCALING_EC2_INSTANCES: Annotated[
        EC2InstancesSettings | None,
        Field(json_schema_extra={"auto_default_from_env": True}),
    ]

    AUTOSCALING_NODES_MONITORING: Annotated[
        NodesMonitoringSettings | None,
        Field(json_schema_extra={"auto_default_from_env": True}),
    ]

    AUTOSCALING_POLL_INTERVAL: Annotated[
        datetime.timedelta,
        Field(
            description="interval between each resource check "
            "(default to seconds, or see https://pydantic-docs.helpmanual.io/usage/types/#datetime-types for string formating)",
        ),
    ] = datetime.timedelta(seconds=10)

    AUTOSCALING_RABBITMQ: Annotated[
        RabbitSettings | None, Field(json_schema_extra={"auto_default_from_env": True})
    ]

    AUTOSCALING_REDIS: Annotated[
        RedisSettings, Field(json_schema_extra={"auto_default_from_env": True})
    ]

    AUTOSCALING_REGISTRY: Annotated[
        RegistrySettings | None,
        Field(json_schema_extra={"auto_default_from_env": True}),
    ]

    AUTOSCALING_DASK: Annotated[
        DaskMonitoringSettings | None,
        Field(json_schema_extra={"auto_default_from_env": True}),
    ]

    AUTOSCALING_PROMETHEUS_INSTRUMENTATION_ENABLED: bool = True

    AUTOSCALING_DRAIN_NODES_WITH_LABELS: Annotated[
        bool,
        Field(
            description="If true, drained nodes"
            " are maintained as active (in the docker terminology) "
            "but a docker node label named osparc-services-ready is attached",
        ),
    ] = False
    AUTOSCALING_TRACING: Annotated[
        TracingSettings | None,
        Field(
            description="settings for opentelemetry tracing",
            json_schema_extra={"auto_default_from_env": True},
        ),
    ]

    AUTOSCALING_DOCKER_JOIN_DRAINED: Annotated[
        bool,
        Field(
            description="If true, new nodes join the swarm as drained. If false as active.",
        ),
    ] = True

    AUTOSCALING_WAIT_FOR_CLOUD_INIT_BEFORE_WARM_BUFFER_ACTIVATION: Annotated[
        bool,
        Field(
            description="If True, then explicitely wait for cloud-init process to be completed before issuing commands. "
            "TIP: might be useful when cheap machines are used",
        ),
    ] = False

    @cached_property
    def log_level(self) -> LogLevelInt:
        return cast(LogLevelInt, self.AUTOSCALING_LOGLEVEL)

    @field_validator("AUTOSCALING_LOGLEVEL", mode="before")
    @classmethod
    def _valid_log_level(cls, value: str) -> str:
        return cls.validate_log_level(value)

    @model_validator(mode="after")
    def _exclude_both_dynamic_computational_mode(self) -> Self:
        if (
            self.AUTOSCALING_DASK is not None
            and self.AUTOSCALING_NODES_MONITORING is not None
        ):
            msg = "Autoscaling cannot be set to monitor both computational and dynamic services (both AUTOSCALING_DASK and AUTOSCALING_NODES_MONITORING are currently set!)"
            raise ValueError(msg)
        return self


def get_application_settings(app: FastAPI) -> ApplicationSettings:
    return cast(ApplicationSettings, app.state.settings)
