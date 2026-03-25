# /src/data/load_raw.py
import pandas as pd

try:
    from config import DATA_RAW
except ImportError:
    from src.config import DATA_RAW

# load `orders` table
def load_orders():
    return pd.read_csv(
        DATA_RAW / "olist_orders_dataset.csv",
        parse_dates=[
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    
# load `items` table
def load_items():
    return pd.read_csv(
        DATA_RAW / "olist_order_items_dataset.csv",
        parse_dates=["shipping_limit_date"],
    )
    
# load `reviews` table
def load_reviews():
    return pd.read_csv(
        DATA_RAW / "olist_order_reviews_dataset.csv",
        parse_dates=["review_creation_date", "review_answer_timestamp"],
    )
    
# load `sellers` table
def load_sellers():
    return pd.read_csv(DATA_RAW / "olist_sellers_dataset.csv")

# load `customers` table
def load_customers():
    return pd.read_csv(DATA_RAW / "olist_customers_dataset.csv")
# load `payments` table
def load_payments():
    return pd.read_csv(DATA_RAW / "olist_order_payments_dataset.csv")

# load `products` table
def load_products():
    temp_1 = pd.read_csv(DATA_RAW / "olist_products_dataset.csv")
    temp_2 = pd.read_csv(DATA_RAW / "product_category_name_translation.csv")
    products = temp_1.merge(
        temp_2,
        on = "product_category_name",
        how = "left"
    )
    return products

# load `geolocation` table
def load_geolocation():
    return pd.read_csv(DATA_RAW / "olist_geolocation_dataset.csv")