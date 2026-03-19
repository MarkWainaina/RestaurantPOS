# Data persistence and file handling
import json
import os
from config import ORDERS_HISTORY_FILE


def save_order(order, payment_method):
    """Save order to file"""
    order_data = {
        "order_id": order.order_id,
        "employee_id": order.employee_id,
        "employee_name": order.employee_name,
        "timestamp": order.timestamp.isoformat(),
        "payment_method": payment_method,
        "items": [(item.name, qty) for item, qty in order.items],
        "total": order.get_total() * 1.10
    }
    
    orders = []
    if os.path.exists(ORDERS_HISTORY_FILE):
        with open(ORDERS_HISTORY_FILE, "r") as f:
            orders = json.load(f)
    
    orders.append(order_data)
    
    with open(ORDERS_HISTORY_FILE, "w") as f:
        json.dump(orders, f, indent=2)


def load_order_history():
    """Load order history from file"""
    if not os.path.exists(ORDERS_HISTORY_FILE):
        return []
    
    with open(ORDERS_HISTORY_FILE, "r") as f:
        return json.load(f)
