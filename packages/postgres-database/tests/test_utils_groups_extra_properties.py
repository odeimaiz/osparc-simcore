# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable
# pylint: disable=too-many-arguments

import random
from collections.abc import AsyncIterator, Awaitable, Callable

import aiopg.sa
import pytest
import sqlalchemy
from aiopg.sa.result import RowProxy
from faker import Faker
from simcore_postgres_database.models.groups import GroupType, groups, user_to_groups
from simcore_postgres_database.models.groups_extra_properties import (
    groups_extra_properties,
)
from simcore_postgres_database.utils_groups_extra_properties import (
    GroupExtraProperties,
    GroupExtraPropertiesNotFoundError,
    GroupExtraPropertiesRepo,
)
from sqlalchemy import literal_column
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine


async def test_get_raises_if_not_found(
    asyncpg_engine: AsyncEngine,
    faker: Faker,
):
    with pytest.raises(GroupExtraPropertiesNotFoundError):
        await GroupExtraPropertiesRepo.get_v2(
            asyncpg_engine,
            gid=faker.pyint(min_value=1),
            product_name=faker.pystr(),
        )


@pytest.fixture
async def registered_user(
    connection: aiopg.sa.connection.SAConnection,
    create_fake_user: Callable[..., Awaitable[RowProxy]],
):
    return await create_fake_user(connection)


@pytest.fixture
def product_name(faker: Faker) -> str:
    return faker.pystr()


@pytest.fixture
async def create_fake_group_extra_properties(
    connection: aiopg.sa.connection.SAConnection,
) -> AsyncIterator[Callable[..., Awaitable[GroupExtraProperties]]]:
    created_properties = []

    async def _creator(
        gid: int, product_name: str, **group_extra_properties_kwars
    ) -> GroupExtraProperties:
        result = await connection.execute(
            sqlalchemy.insert(groups_extra_properties)
            .values(
                group_id=gid, product_name=product_name, **group_extra_properties_kwars
            )
            .returning(literal_column("*"))
        )
        assert result
        row = await result.first()
        assert row
        properties = GroupExtraProperties.from_row(row)
        created_properties.append((properties.group_id, properties.product_name))
        return properties

    yield _creator

    for group_id, product_name in created_properties:
        await connection.execute(
            sqlalchemy.delete(groups_extra_properties).where(
                (groups_extra_properties.c.group_id == group_id)
                & (groups_extra_properties.c.product_name == product_name)
            )
        )


async def test_get_v2(
    asyncpg_engine: AsyncEngine,
    registered_user: RowProxy,
    product_name: str,
    create_fake_product: Callable[[str], Awaitable[Row]],
    create_fake_group_extra_properties: Callable[..., Awaitable[GroupExtraProperties]],
):
    with pytest.raises(GroupExtraPropertiesNotFoundError):
        await GroupExtraPropertiesRepo.get_v2(
            asyncpg_engine, gid=registered_user.primary_gid, product_name=product_name
        )

    await create_fake_product(product_name)
    created_extra_properties = await create_fake_group_extra_properties(
        registered_user.primary_gid, product_name
    )
    received_extra_properties = await GroupExtraPropertiesRepo.get_v2(
        asyncpg_engine, gid=registered_user.primary_gid, product_name=product_name
    )
    assert created_extra_properties == received_extra_properties


@pytest.fixture
async def everyone_group_id(connection: aiopg.sa.connection.SAConnection) -> int:
    result = await connection.scalar(
        sqlalchemy.select(groups.c.gid).where(groups.c.type == GroupType.EVERYONE)
    )
    assert result
    return result


async def test_get_aggregated_properties_for_user_with_no_entries_raises(
    connection_factory: aiopg.sa.connection.SAConnection | AsyncConnection,
    product_name: str,
    registered_user: RowProxy,
):
    with pytest.raises(GroupExtraPropertiesNotFoundError):
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )


async def _add_user_to_group(
    connection: aiopg.sa.connection.SAConnection | AsyncConnection,
    *,
    user_id: int,
    group_id: int,
) -> None:
    await connection.execute(
        sqlalchemy.insert(user_to_groups).values(uid=user_id, gid=group_id)
    )


async def test_get_aggregated_properties_for_user_returns_properties_in_expected_priority(
    connection: aiopg.sa.connection.SAConnection,
    connection_factory: aiopg.sa.connection.SAConnection | AsyncConnection,
    product_name: str,
    registered_user: RowProxy,
    create_fake_product: Callable[[str], Awaitable[Row]],
    create_fake_group: Callable[..., Awaitable[RowProxy]],
    create_fake_group_extra_properties: Callable[..., Awaitable[GroupExtraProperties]],
    everyone_group_id: int,
):
    await create_fake_product(product_name)
    await create_fake_product(f"{product_name}_additional_just_for_fun")

    # let's create a few groups
    created_groups = [await create_fake_group(connection) for _ in range(5)]

    # create a specific extra properties for group everyone
    everyone_group_extra_properties = await create_fake_group_extra_properties(
        everyone_group_id, product_name
    )

    # this should return the everyone group properties
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties == everyone_group_extra_properties

    # let's add the user in these groups
    for group in created_groups:
        await _add_user_to_group(
            connection_factory, user_id=registered_user.id, group_id=group.gid
        )

    # this changes nothing
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties == everyone_group_extra_properties

    # now create some extra properties
    standard_group_extra_properties = [
        await create_fake_group_extra_properties(group.gid, product_name)
        for group in created_groups
    ]

    # this returns the last properties created
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties != everyone_group_extra_properties
    assert aggregated_group_properties == standard_group_extra_properties[0]

    # now create some personal extra properties
    personal_group_extra_properties = await create_fake_group_extra_properties(
        registered_user.primary_gid, product_name
    )
    # this now returns the primary properties
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties == personal_group_extra_properties


async def test_get_aggregated_properties_for_user_returns_properties_in_expected_priority_without_everyone_group(
    connection: aiopg.sa.connection.SAConnection,
    connection_factory: aiopg.sa.connection.SAConnection | AsyncConnection,
    product_name: str,
    registered_user: RowProxy,
    create_fake_product: Callable[[str], Awaitable[Row]],
    create_fake_group: Callable[..., Awaitable[RowProxy]],
    create_fake_group_extra_properties: Callable[..., Awaitable[GroupExtraProperties]],
    everyone_group_id: int,
):
    await create_fake_product(product_name)
    await create_fake_product(f"{product_name}_additional_just_for_fun")

    # let's create a few groups
    created_groups = [await create_fake_group(connection) for _ in range(5)]
    # let's add the user in these groups
    for group in created_groups:
        await _add_user_to_group(
            connection_factory, user_id=registered_user.id, group_id=group.gid
        )

    # now create some extra properties
    standard_group_extra_properties = [
        await create_fake_group_extra_properties(group.gid, product_name)
        for group in created_groups
    ]

    # this returns the last properties created
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties == standard_group_extra_properties[0]

    # now create some personal extra properties
    personal_group_extra_properties = await create_fake_group_extra_properties(
        registered_user.primary_gid, product_name
    )
    # this now returns the primary properties
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties == personal_group_extra_properties


async def test_get_aggregated_properties_for_user_returns_property_values_as_truthy_if_one_of_them_is(
    connection: aiopg.sa.connection.SAConnection,
    connection_factory: aiopg.sa.connection.SAConnection | AsyncConnection,
    product_name: str,
    registered_user: RowProxy,
    create_fake_product: Callable[[str], Awaitable[Row]],
    create_fake_group: Callable[..., Awaitable[RowProxy]],
    create_fake_group_extra_properties: Callable[..., Awaitable[GroupExtraProperties]],
    everyone_group_id: int,
):
    await create_fake_product(product_name)
    await create_fake_product(f"{product_name}_additional_just_for_fun")

    # create a specific extra properties for group that disallow everything
    everyone_group_extra_properties = await create_fake_group_extra_properties(
        everyone_group_id,
        product_name,
        internet_access=False,
        override_services_specifications=False,
        use_on_demand_clusters=False,
    )
    # this should return the everyone group properties
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties == everyone_group_extra_properties

    # now we create some standard groups and add the user to them and make everything false for now
    standard_groups = [await create_fake_group(connection) for _ in range(5)]
    for group in standard_groups:
        await create_fake_group_extra_properties(
            group.gid,
            product_name,
            internet_access=False,
            override_services_specifications=False,
            use_on_demand_clusters=False,
        )
        await _add_user_to_group(
            connection_factory, user_id=registered_user.id, group_id=group.gid
        )

    # now we still should not have any of these value Truthy
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties.internet_access is False
    assert aggregated_group_properties.override_services_specifications is False
    assert aggregated_group_properties.use_on_demand_clusters is False

    # let's change one of these standard groups
    random_standard_group = random.choice(standard_groups)  # noqa: S311
    result = await connection.execute(
        groups_extra_properties.update()
        .where(groups_extra_properties.c.group_id == random_standard_group.gid)
        .values(internet_access=True)
    )
    assert result.rowcount == 1

    # now we should have internet access
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties.internet_access is True
    assert aggregated_group_properties.override_services_specifications is False
    assert aggregated_group_properties.use_on_demand_clusters is False

    # let's change another one of these standard groups
    random_standard_group = random.choice(standard_groups)  # noqa: S311
    result = await connection.execute(
        groups_extra_properties.update()
        .where(groups_extra_properties.c.group_id == random_standard_group.gid)
        .values(override_services_specifications=True)
    )
    assert result.rowcount == 1

    # now we should have internet access and service override
    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties.internet_access is True
    assert aggregated_group_properties.override_services_specifications is True
    assert aggregated_group_properties.use_on_demand_clusters is False

    # and we can deny it again by setting a primary extra property
    # now create some personal extra properties
    personal_group_extra_properties = await create_fake_group_extra_properties(
        registered_user.primary_gid,
        product_name,
        internet_access=False,
        use_on_demand_clusters=True,
    )
    assert personal_group_extra_properties

    aggregated_group_properties = (
        await GroupExtraPropertiesRepo.get_aggregated_properties_for_user(
            connection_factory, user_id=registered_user.id, product_name=product_name
        )
    )
    assert aggregated_group_properties.internet_access is False
    assert aggregated_group_properties.override_services_specifications is False
    assert aggregated_group_properties.use_on_demand_clusters is True
