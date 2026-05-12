from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from src.application.services.shipping_service import ShipmentNotFoundError
from src.domain.shipping.shipment import AlreadyDeliveredError
from src.infrastructure.composition import RequestScope
from src.presentation.api.dependencies import get_scope
from src.presentation.api.schemas import ShipmentOverviewRead, ShipmentRead

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("/active", response_model=list[ShipmentOverviewRead])
async def active_shipments(
    scope: RequestScope = Depends(get_scope),
) -> list[ShipmentOverviewRead]:
    now = _utcnow()
    shipments = await scope.shipping.list_active_shipments()
    return [ShipmentOverviewRead.from_domain(shipment, now=now) for shipment in shipments]


@router.get("/delayed", response_model=list[ShipmentOverviewRead])
async def delayed_shipments(
    scope: RequestScope = Depends(get_scope),
) -> list[ShipmentOverviewRead]:
    now = _utcnow()
    shipments = await scope.shipping.find_delayed_shipments(now=now)
    return [ShipmentOverviewRead.from_domain(shipment, now=now) for shipment in shipments]


@router.get("/by-order/{order_id}", response_model=ShipmentRead)
async def shipment_by_order(
    order_id: int, scope: RequestScope = Depends(get_scope)
) -> ShipmentRead:
    try:
        shipment = await scope.shipping.get_by_order(order_id)
    except ShipmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ShipmentRead.from_domain(shipment)


@router.post("/{shipment_id}/delivered", response_model=ShipmentRead)
async def mark_delivered(
    shipment_id: int,
    scope: RequestScope = Depends(get_scope),
) -> ShipmentRead:
    try:
        shipment = await scope.shipping.mark_delivered(shipment_id, at=_utcnow())
    except ShipmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AlreadyDeliveredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ShipmentRead.from_domain(shipment)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)
