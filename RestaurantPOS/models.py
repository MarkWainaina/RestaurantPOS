# Data models for the POS system
from datetime import datetime


class MenuItem:
    """Represents a menu item (food or drink)"""
    def __init__(self, item_id, name, price, category):
        self.item_id = item_id
        self.name = name
        self.price = price
        self.category = category
    
    def __repr__(self):
        return f"{self.name} - ${self.price:.2f}"


class Order:
    """Represents a customer order"""
    def __init__(self, order_id, employee_id, employee_name):
        self.order_id = order_id
        self.employee_id = employee_id
        self.employee_name = employee_name
        self.items = []  # List of (MenuItem, quantity) tuples
        self.timestamp = datetime.now()
        self.status = "pending"
    
    def add_item(self, menu_item, quantity):
        """Add item to order"""
        self.items.append((menu_item, quantity))
    
    def remove_item(self, index):
        """Remove item from order"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
    
    def get_total(self):
        """Calculate order total (before tax)"""
        return sum(item.price * qty for item, qty in self.items)
    
    def get_itemized(self):
        """Return itemized breakdown"""
        return [(item.name, qty, item.price * qty) for item, qty in self.items]
