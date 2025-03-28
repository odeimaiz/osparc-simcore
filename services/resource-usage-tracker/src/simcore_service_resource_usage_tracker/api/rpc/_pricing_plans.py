from fastapi import FastAPI
from models_library.api_schemas_resource_usage_tracker.pricing_plans import (
    PricingPlanToServiceGet,
    RutPricingPlanGet,
    RutPricingPlanPage,
    RutPricingUnitGet,
)
from models_library.products import ProductName
from models_library.resource_tracker import (
    PricingPlanCreate,
    PricingPlanId,
    PricingPlanUpdate,
    PricingUnitId,
    PricingUnitWithCostCreate,
    PricingUnitWithCostUpdate,
)
from models_library.services import ServiceKey, ServiceVersion
from servicelib.rabbitmq import RPCRouter
from servicelib.rabbitmq.rpc_interfaces.resource_usage_tracker.errors import (
    PricingUnitDuplicationError,
)

from ...services import pricing_plans, pricing_units

router = RPCRouter()


## Pricing plans


@router.expose(reraise_if_error_type=())
async def get_pricing_plan(
    app: FastAPI,
    *,
    product_name: ProductName,
    pricing_plan_id: PricingPlanId,
) -> RutPricingPlanGet:
    return await pricing_plans.get_pricing_plan(
        product_name=product_name,
        pricing_plan_id=pricing_plan_id,
        db_engine=app.state.engine,
    )


@router.expose(reraise_if_error_type=())
async def list_pricing_plans_without_pricing_units(
    app: FastAPI,
    *,
    product_name: ProductName,
    exclude_inactive: bool,
    # pagination
    offset: int,
    limit: int,
) -> RutPricingPlanPage:
    return await pricing_plans.list_pricing_plans_without_pricing_units(
        db_engine=app.state.engine,
        product_name=product_name,
        exclude_inactive=exclude_inactive,
        offset=offset,
        limit=limit,
    )


@router.expose(reraise_if_error_type=())
async def create_pricing_plan(
    app: FastAPI,
    *,
    data: PricingPlanCreate,
) -> RutPricingPlanGet:
    return await pricing_plans.create_pricing_plan(
        data=data,
        db_engine=app.state.engine,
    )


@router.expose(reraise_if_error_type=())
async def update_pricing_plan(
    app: FastAPI,
    *,
    product_name: ProductName,
    data: PricingPlanUpdate,
) -> RutPricingPlanGet:
    return await pricing_plans.update_pricing_plan(
        product_name=product_name,
        data=data,
        db_engine=app.state.engine,
    )


## Pricing units


@router.expose(reraise_if_error_type=())
async def get_pricing_unit(
    app: FastAPI,
    *,
    product_name: ProductName,
    pricing_plan_id: PricingPlanId,
    pricing_unit_id: PricingUnitId,
) -> RutPricingUnitGet:
    return await pricing_units.get_pricing_unit(
        product_name=product_name,
        pricing_plan_id=pricing_plan_id,
        pricing_unit_id=pricing_unit_id,
        db_engine=app.state.engine,
    )


@router.expose(reraise_if_error_type=(PricingUnitDuplicationError,))
async def create_pricing_unit(
    app: FastAPI,
    *,
    product_name: ProductName,
    data: PricingUnitWithCostCreate,
) -> RutPricingUnitGet:
    return await pricing_units.create_pricing_unit(
        product_name=product_name,
        data=data,
        db_engine=app.state.engine,
    )


@router.expose(reraise_if_error_type=())
async def update_pricing_unit(
    app: FastAPI,
    *,
    product_name: ProductName,
    data: PricingUnitWithCostUpdate,
) -> RutPricingUnitGet:
    return await pricing_units.update_pricing_unit(
        product_name=product_name,
        data=data,
        db_engine=app.state.engine,
    )


## Pricing plan to service


@router.expose(reraise_if_error_type=())
async def list_connected_services_to_pricing_plan_by_pricing_plan(
    app: FastAPI,
    *,
    product_name: ProductName,
    pricing_plan_id: PricingPlanId,
) -> list[PricingPlanToServiceGet]:
    output: list[
        PricingPlanToServiceGet
    ] = await pricing_plans.list_connected_services_to_pricing_plan_by_pricing_plan(
        product_name=product_name,
        pricing_plan_id=pricing_plan_id,
        db_engine=app.state.engine,
    )
    return output


@router.expose(reraise_if_error_type=())
async def connect_service_to_pricing_plan(
    app: FastAPI,
    *,
    product_name: ProductName,
    pricing_plan_id: PricingPlanId,
    service_key: ServiceKey,
    service_version: ServiceVersion,
) -> PricingPlanToServiceGet:
    return await pricing_plans.connect_service_to_pricing_plan(
        product_name=product_name,
        pricing_plan_id=pricing_plan_id,
        service_key=service_key,
        service_version=service_version,
        db_engine=app.state.engine,
    )
