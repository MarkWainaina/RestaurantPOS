# Configuration and data constants

# Menu items configuration
MENU_ITEMS = [
    {"id": 1, "name": "Burger", "price": 9.99, "category": "Food"},
    {"id": 2, "name": "Pizza", "price": 12.99, "category": "Food"},
    {"id": 3, "name": "Pasta", "price": 10.99, "category": "Food"},
    {"id": 4, "name": "Chicken Wings", "price": 8.99, "category": "Food"},
    {"id": 5, "name": "Salad", "price": 7.99, "category": "Food"},
    {"id": 6, "name": "Coca-Cola", "price": 2.99, "category": "Drink"},
    {"id": 7, "name": "Iced Tea", "price": 2.49, "category": "Drink"},
    {"id": 8, "name": "Coffee", "price": 3.49, "category": "Drink"},
    {"id": 9, "name": "Lemonade", "price": 2.99, "category": "Drink"},
    {"id": 10, "name": "Water", "price": 1.99, "category": "Drink"},
]

# Employees configuration
EMPLOYEES = {
    "E001": {"name": "John Smith", "position": "Server"},
    "E002": {"name": "Sarah Johnson", "position": "Server"},
    "E003": {"name": "Mike Brown", "position": "Cashier"},
    "E004": {"name": "Emma Davis", "position": "Manager"},
}

# Payment methods
PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card", "Check"]

# File paths
ORDERS_HISTORY_FILE = "orders_history.json"
