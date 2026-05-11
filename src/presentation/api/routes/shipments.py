from fastapi import APIRouter, Depends, HTTPException

from src.application.services.shipping_service import ShipmentNotFoundError
from src.infrastructure.composition import RequestScope
from src.presentation.api.dependencies import get_scope
from src.presentation.api.schemas import ShipmentRead

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("/by-order/{order_id}", response_model=ShipmentRead)
async def shipment_by_order(
    order_id: int, scope: RequestScope = Depends(get_scope)
) -> ShipmentRead:
    try:
        shipment = await scope.shipping.get_by_order(order_id)
    except ShipmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ShipmentRead.from_domain(shipment)
