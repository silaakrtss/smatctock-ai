from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from src.agent.tools.registry import ToolRegistry
from src.agent.tools.tool_result import ToolResult
from src.application.services.notification_service import NotificationService
from src.application.services.order_service import OrderService
from src.application.services.shipping_service import ShippingService
from src.application.services.stock_service import StockService
from src.domain.notifications.notification import NotificationChannel
from src.domain.orders.order import Order
from src.domain.products.product import Product
from src.domain.shipping.shipment import Shipment

Handler = Callable[[dict[str, Any]], Awaitable[ToolResult]]


def register_default_tools(
    *,
    registry: ToolRegistry,
    stock: StockService,
    orders: OrderService,
    shipping: ShippingService,
    notifications: NotificationService,
) -> None:
    registry.register("get_product_stock", _build_get_product_stock(stock))
    registry.register("list_low_stock_products", _build_list_low_stock(stock))
    registry.register("get_order_status", _build_get_order_status(orders))
    registry.register("list_orders", _build_list_orders(orders))
    registry.register("get_shipment_status", _build_get_shipment_status(shipping))
    registry.register("list_delayed_shipments", _build_list_delayed(shipping))
    registry.register("notify_customer", _build_notify_customer(notifications))
    registry.register("create_reorder_draft", _build_create_reorder_draft(stock))


def _build_get_product_stock(stock: StockService) -> Handler:
    async def handler(args: dict[str, Any]) -> ToolResult:
        product = await stock.get_by_name(args["product_name"])
        # inventory_overview'dan eşik ve durum bilgisini de al
        overview = await stock.inventory_overview()
        item = next((i for i in overview if i.product.id == product.id), None)
        payload = _product_payload(product)
        if item is not None:
            payload["min_quantity"] = item.min_quantity
            payload["status"] = item.status
        return ToolResult.success(payload)

    return handler


def _build_list_low_stock(stock: StockService) -> Handler:
    async def handler(args: dict[str, Any]) -> ToolResult:
        items = await stock.find_below_threshold()
        return ToolResult.success({"products": [_product_payload(p) for p in items]})

    return handler


def _build_get_order_status(orders: OrderService) -> Handler:
    async def handler(args: dict[str, Any]) -> ToolResult:
        order = await orders.get_order(int(args["order_id"]))
        return ToolResult.success(_order_payload(order))

    return handler


def _build_list_orders(orders: OrderService) -> Handler:
    async def handler(args: dict[str, Any]) -> ToolResult:
        day = _parse_iso_date(args.get("date"))
        result = await orders.list(
            status=args.get("status"),
            day=day,
            customer_name=args.get("customer_name"),
        )
        return ToolResult.success({"orders": [_order_payload(o) for o in result]})

    return handler


def _build_get_shipment_status(shipping: ShippingService) -> Handler:
    async def handler(args: dict[str, Any]) -> ToolResult:
        shipment = await shipping.get_by_order(int(args["order_id"]))
        return ToolResult.success(_shipment_payload(shipment))

    return handler


def _build_list_delayed(shipping: ShippingService) -> Handler:
    async def handler(args: dict[str, Any]) -> ToolResult:
        delayed = await shipping.find_delayed_shipments(now=datetime.now().astimezone())
        return ToolResult.success({"shipments": [_shipment_payload(s) for s in delayed]})

    return handler


def _build_notify_customer(notifications: NotificationService) -> Handler:
    async def handler(args: dict[str, Any]) -> ToolResult:
        notification = await notifications.notify_customer(
            order_id=int(args["order_id"]),
            recipient=str(args["recipient"]),
            message=str(args["message"]),
            channel=NotificationChannel.TELEGRAM,
        )
        return ToolResult.success(
            {"notification_id": notification.id, "status": notification.status.value}
        )

    return handler


def _build_create_reorder_draft(stock: StockService) -> Handler:
    async def handler(args: dict[str, Any]) -> ToolResult:
        notification = await stock.create_reorder_draft(
            product_id=int(args["product_id"]),
            quantity=int(args["quantity"]),
        )
        return ToolResult.success(
            {"notification_id": notification.id, "status": notification.status.value}
        )

    return handler


def _product_payload(product: Product) -> dict[str, Any]:
    return {"id": product.id, "name": product.name, "stock": product.stock}


def _order_payload(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "status": order.status.value,
        "created_at": order.created_at.isoformat(),
    }


def _shipment_payload(shipment: Shipment) -> dict[str, Any]:
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "carrier": shipment.carrier,
        "tracking_number": shipment.tracking_number,
        "status": shipment.status.value,
        "expected_delivery_at": shipment.expected_delivery_at.isoformat(),
        "delivered_at": (shipment.delivered_at.isoformat() if shipment.delivered_at else None),
    }


def _parse_iso_date(raw: Any) -> datetime | None:
    if not raw:
        return None
    return datetime.fromisoformat(str(raw))
