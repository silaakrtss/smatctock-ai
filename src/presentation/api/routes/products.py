from fastapi import APIRouter, Depends

from src.infrastructure.composition import RequestScope
from src.presentation.api.dependencies import get_scope
from src.presentation.api.schemas import ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
async def list_products(scope: RequestScope = Depends(get_scope)) -> list[ProductRead]:
    products = await scope.stock.products.list_all()
    return [ProductRead.from_domain(p) for p in products]
