from enum import StrEnum


class SemanticRole(StrEnum):
    date = "date"
    timestamp = "timestamp"
    revenue = "revenue"
    spend = "spend"
    channel = "channel"
    campaign = "campaign"
    impressions = "impressions"
    clicks = "clicks"
    conversions = "conversions"
    orders = "orders"
    units_sold = "units_sold"
    price = "price"
    discount = "discount"
    cost = "cost"
    profit = "profit"
    roas = "roas"
    ctr = "ctr"
    cpc = "cpc"
    cpa = "cpa"
    conversion_rate = "conversion_rate"
    customer_id = "customer_id"
    product_id = "product_id"
    product_name = "product_name"
    product_category = "product_category"
    geography = "geography"
    country = "country"
    region = "region"
    city = "city"
    device = "device"
    source = "source"
    medium = "medium"
    sessions = "sessions"
    users = "users"
    inventory = "inventory"
    promotion = "promotion"
    holiday = "holiday"
    target = "target"
    identifier = "identifier"
    descriptive_text = "descriptive_text"
    ignored = "ignored"
    unknown = "unknown"


ROLE_SYNONYMS: dict[SemanticRole, set[str]] = {
    SemanticRole.date: {
        "date",
        "order_date",
        "transaction_date",
        "event_date",
        "campaign_date",
        "day",
        "week",
        "month",
    },
    SemanticRole.timestamp: {"timestamp", "datetime", "event_time", "created_at", "time"},
    SemanticRole.revenue: {
        "revenue",
        "sales",
        "sales_amount",
        "total_sales",
        "gross_sales",
        "net_sales",
        "turnover",
        "gm_value",
        "gmv",
        "order_value",
    },
    SemanticRole.spend: {
        "spend",
        "ad_spend",
        "advertising_cost",
        "marketing_cost",
        "media_spend",
        "campaign_spend",
        "budget_spent",
    },
    SemanticRole.channel: {"channel", "marketing_channel", "platform", "network", "traffic_channel"},
    SemanticRole.campaign: {"campaign", "campaign_name", "campaign_id", "ad_group", "promotion_name"},
    SemanticRole.impressions: {"impressions", "ad_impressions", "views", "served"},
    SemanticRole.clicks: {"clicks", "ad_clicks", "link_clicks"},
    SemanticRole.conversions: {"conversions", "purchases", "leads", "signups", "completed_actions"},
    SemanticRole.orders: {"orders", "order_count", "transactions"},
    SemanticRole.units_sold: {"units_sold", "quantity", "qty"},
    SemanticRole.price: {"price", "unit_price", "selling_price"},
    SemanticRole.discount: {"discount", "discount_rate"},
    SemanticRole.cost: {"cost", "unit_cost", "cogs"},
    SemanticRole.profit: {"profit", "margin", "gross_profit"},
    SemanticRole.roas: {"roas", "return_on_ad_spend"},
    SemanticRole.ctr: {"ctr", "click_through_rate"},
    SemanticRole.cpc: {"cpc", "cost_per_click"},
    SemanticRole.cpa: {"cpa", "cost_per_acquisition"},
    SemanticRole.conversion_rate: {"conversion_rate", "cvr"},
    SemanticRole.customer_id: {"customer_id", "customer_key"},
    SemanticRole.product_id: {"product_id", "sku", "item_id"},
    SemanticRole.product_name: {"product_name", "item_name"},
    SemanticRole.product_category: {"product_category", "category"},
    SemanticRole.geography: {"geography", "location", "geo"},
    SemanticRole.country: {"country"},
    SemanticRole.region: {"region", "state"},
    SemanticRole.city: {"city"},
    SemanticRole.device: {"device", "device_type"},
    SemanticRole.source: {"source", "utm_source"},
    SemanticRole.medium: {"medium", "utm_medium"},
    SemanticRole.sessions: {"sessions", "visits"},
    SemanticRole.users: {"users", "visitors"},
    SemanticRole.inventory: {"inventory", "stock"},
    SemanticRole.promotion: {"promotion", "promo", "is_promotion"},
    SemanticRole.holiday: {"holiday", "is_holiday"},
    SemanticRole.target: {"target", "label", "outcome"},
    SemanticRole.identifier: {"id", "identifier", "key"},
    SemanticRole.descriptive_text: {"description", "notes", "text"},
}

ROLE_DESCRIPTIONS = {role: role.value.replace("_", " ").title() for role in SemanticRole}
