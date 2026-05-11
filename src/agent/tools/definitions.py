from src.application.ports.llm_client import ToolDefinition

TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_product_stock",
        description=(
            "Bir ürünün güncel stok miktarını döner. "
            "Kullanıcı belirli bir ürünün stoğunu sorduğunda kullan."
        ),
        parameters={
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Ürün adı (örn. 'Domates').",
                },
            },
            "required": ["product_name"],
        },
    ),
    ToolDefinition(
        name="list_low_stock_products",
        description=(
            "Eşik altı stoğu olan ürünleri listeler. "
            "Kullanıcı 'düşük stok' veya 'az kalan' sorularında kullan."
        ),
        parameters={"type": "object", "properties": {}, "required": []},
    ),
    ToolDefinition(
        name="get_order_status",
        description=(
            "Belirli bir siparişin durumunu döner. Kullanıcı sipariş numarası verirse kullan."
        ),
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "Sipariş kimliği."},
            },
            "required": ["order_id"],
        },
    ),
    ToolDefinition(
        name="list_orders",
        description=(
            "Siparişleri opsiyonel filtrelerle listeler (durum, tarih ISO formatı, müşteri adı)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "preparing/in_shipping/delivered/cancelled",
                },
                "date": {"type": "string", "description": "ISO tarih (YYYY-MM-DD)."},
                "customer_name": {"type": "string"},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_shipment_status",
        description="Bir siparişin kargo durumunu döner.",
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "integer"},
            },
            "required": ["order_id"],
        },
    ),
    ToolDefinition(
        name="list_delayed_shipments",
        description="Beklenen teslim tarihi geçmiş ve hala yolda olan kargoları listeler.",
        parameters={"type": "object", "properties": {}, "required": []},
    ),
    ToolDefinition(
        name="notify_customer",
        description=(
            "Müşteriye sipariş hakkında bildirim gönderir. "
            "Yöneticinin onayı varsa veya kullanıcı açıkça istediyse kullan."
        ),
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "integer"},
                "recipient": {"type": "string", "description": "Kanal adresi (örn. @ali)."},
                "message": {"type": "string"},
            },
            "required": ["order_id", "recipient", "message"],
        },
    ),
    ToolDefinition(
        name="create_reorder_draft",
        description=(
            "Eşik altı bir ürün için tedarikçiye sipariş taslağı bildirimi gönderir. "
            "Kullanıcı stok yenileme istediğinde kullan."
        ),
        parameters={
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "quantity": {"type": "integer", "description": "Sipariş edilecek adet."},
            },
            "required": ["product_id", "quantity"],
        },
    ),
]
