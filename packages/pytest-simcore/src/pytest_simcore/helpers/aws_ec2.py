import base64
from typing import Sequence

from types_aiobotocore_ec2 import EC2Client
from types_aiobotocore_ec2.literals import InstanceStateNameType, InstanceTypeType
from types_aiobotocore_ec2.type_defs import FilterTypeDef, InstanceTypeDef


async def assert_autoscaled_computational_ec2_instances(
    ec2_client: EC2Client,
    *,
    expected_num_reservations: int,
    expected_num_instances: int,
    expected_instance_type: InstanceTypeType,
    expected_instance_state: InstanceStateNameType,
) -> list[InstanceTypeDef]:
    return await assert_ec2_instances(
        ec2_client,
        expected_num_reservations=expected_num_reservations,
        expected_num_instances=expected_num_instances,
        expected_instance_type=expected_instance_type,
        expected_instance_state=expected_instance_state,
        expected_instance_tag_keys=[
            "io.simcore.autoscaling.dask-scheduler_url",
            "user_id",
            "wallet_id",
            "osparc-tag",
        ],
        expected_user_data=["docker swarm join"],
    )


async def assert_autoscaled_dynamic_ec2_instances(
    ec2_client: EC2Client,
    *,
    expected_num_reservations: int,
    expected_num_instances: int,
    expected_instance_type: InstanceTypeType,
    expected_instance_state: InstanceStateNameType,
) -> list[InstanceTypeDef]:
    return await assert_ec2_instances(
        ec2_client,
        expected_num_reservations=expected_num_reservations,
        expected_num_instances=expected_num_instances,
        expected_instance_type=expected_instance_type,
        expected_instance_state=expected_instance_state,
        expected_instance_tag_keys=[
            "io.simcore.autoscaling.monitored_nodes_labels",
            "io.simcore.autoscaling.monitored_services_labels",
            "user_id",
            "wallet_id",
            "osparc-tag",
        ],
        expected_user_data=["docker swarm join"],
    )


async def assert_autoscaled_dynamic_warm_pools_ec2_instances(
    ec2_client: EC2Client,
    *,
    expected_num_reservations: int,
    expected_num_instances: int,
    expected_instance_type: InstanceTypeType,
    expected_instance_state: InstanceStateNameType,
    expected_additional_tag_keys: list[str],
    instance_filters: Sequence[FilterTypeDef] | None,
) -> list[InstanceTypeDef]:
    return await assert_ec2_instances(
        ec2_client,
        expected_num_reservations=expected_num_reservations,
        expected_num_instances=expected_num_instances,
        expected_instance_type=expected_instance_type,
        expected_instance_state=expected_instance_state,
        expected_instance_tag_keys=[
            "io.simcore.autoscaling.monitored_nodes_labels",
            "io.simcore.autoscaling.monitored_services_labels",
            "buffer-machine",
            *expected_additional_tag_keys,
        ],
        expected_user_data=[],
        instance_filters=instance_filters,
    )


async def assert_ec2_instances(
    ec2_client: EC2Client,
    *,
    expected_num_reservations: int,
    expected_num_instances: int,
    expected_instance_type: InstanceTypeType,
    expected_instance_state: InstanceStateNameType,
    expected_instance_tag_keys: list[str],
    expected_user_data: list[str],
    instance_filters: Sequence[FilterTypeDef] | None = None,
) -> list[InstanceTypeDef]:
    list_instances: list[InstanceTypeDef] = []
    all_instances = await ec2_client.describe_instances(Filters=instance_filters or [])
    assert len(all_instances["Reservations"]) == expected_num_reservations
    for reservation in all_instances["Reservations"]:
        assert "Instances" in reservation
        assert (
            len(reservation["Instances"]) == expected_num_instances
        ), f"expected {expected_num_instances}, found {len(reservation['Instances'])}"
        for instance in reservation["Instances"]:
            assert "InstanceType" in instance
            assert instance["InstanceType"] == expected_instance_type
            assert "Tags" in instance
            assert instance["Tags"]
            expected_tag_keys = [
                *expected_instance_tag_keys,
                "io.simcore.autoscaling.version",
                "Name",
            ]
            instance_tag_keys = [tag["Key"] for tag in instance["Tags"] if "Key" in tag]
            for tag_key in instance_tag_keys:
                assert (
                    tag_key in expected_tag_keys
                ), f"instance has additional unexpected {tag_key=} vs {expected_tag_keys=}"
            for tag in expected_instance_tag_keys:
                assert (
                    tag in instance_tag_keys
                ), f"instance missing {tag=} vs {instance_tag_keys=}"

            assert "PrivateDnsName" in instance
            instance_private_dns_name = instance["PrivateDnsName"]
            assert instance_private_dns_name.endswith(".ec2.internal")
            assert "State" in instance
            state = instance["State"]
            assert "Name" in state
            assert state["Name"] == expected_instance_state

            assert "InstanceId" in instance
            user_data = await ec2_client.describe_instance_attribute(
                Attribute="userData", InstanceId=instance["InstanceId"]
            )
            assert "UserData" in user_data
            assert "Value" in user_data["UserData"]
            user_data = base64.b64decode(user_data["UserData"]["Value"]).decode()
            for user_data_string in expected_user_data:
                assert user_data.count(user_data_string) == 1
            list_instances.append(instance)
    return list_instances
