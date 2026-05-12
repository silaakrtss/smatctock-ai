from fastapi import APIRouter, Depends, HTTPException

from src.application.services.stock_service import ProductNotFoundError
from src.domain.products.product import InsufficientStockError, InvalidQuantityError
from src.infrastructure.composition import RequestScope
from src.presentation.api.dependencies import get_scope
from src.presentation.api.schemas import (
    InventoryItemRead,
    NotificationRead,
    ProductRead,
    ReorderDraftRequest,
    StockAdjustmentRequest,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryItemRead])
async def inventory_overview(
    scope: RequestScope = Depends(get_scope),
) -> list[InventoryItemRead]:
    items = await scope.stock.inventory_overview()
    return [InventoryItemRead.from_service(item) for item in items]


@router.get("/low-stock", response_model=list[InventoryItemRead])
async def low_stock_items(
    scope: RequestScope = Depends(get_scope),
) -> list[InventoryItemRead]:
    items = await scope.stock.inventory_overview()
    return [
        InventoryItemRead.from_service(item)
        for item in items
        if item.status in {"low", "out"}
    ]


@router.post("/{product_id}/adjust", response_model=ProductRead)
async def adjust_stock(
    product_id: int,
    request: StockAdjustmentRequest,
    scope: RequestScope = Depends(get_scope),
) -> ProductRead:
    try:
        product = await scope.stock.adjust_stock(product_id=product_id, delta=request.delta)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (InsufficientStockError, InvalidQuantityError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProductRead.from_domain(product)


@router.post("/{product_id}/reorder-draft", response_model=NotificationRead)
async def create_reorder_draft(
    product_id: int,
    request: ReorderDraftRequest,
    scope: RequestScope = Depends(get_scope),
) -> NotificationRead:
    try:
        quantity = request.quantity
        if quantity is None:
            quantity = await _suggested_quantity(scope=scope, product_id=product_id)
        notification = await scope.stock.create_reorder_draft(
            product_id=product_id,
            quantity=quantity,
        )
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return NotificationRead.from_domain(notification)


async def _suggested_quantity(*, scope: RequestScope, product_id: int) -> int:
    items = await scope.stock.inventory_overview()
    for item in items:
        if item.product.id == product_id:
            return item.suggested_reorder_quantity or item.min_quantity or 1
    raise ProductNotFoundError(f"Product {product_id} not found")
