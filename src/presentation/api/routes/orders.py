from fastapi import APIRouter, Depends, HTTPException

from src.application.services.order_service import OrderNotFoundError
from src.infrastructure.composition import RequestScope
from src.presentation.api.dependencies import get_scope
from src.presentation.api.schemas import OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderRead])
async def list_orders(
    status: str | None = None,
    scope: RequestScope = Depends(get_scope),
) -> list[OrderRead]:
    orders = await scope.orders.list(status=status)
    return [OrderRead.from_domain(o) for o in orders]


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, scope: RequestScope = Depends(get_scope)) -> OrderRead:
    try:
        order = await scope.orders.get_order(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OrderRead.from_domain(order)
