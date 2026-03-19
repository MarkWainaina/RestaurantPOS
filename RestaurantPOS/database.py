import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime

# Path to the SQLite database file (in the project directory)
DB_PATH = Path(__file__).with_name("restaurant_pos.db")


@contextmanager
def get_connection():
    """Context manager that yields a SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize_database():
    """Create tables if they don't exist and seed base data."""
    with get_connection() as conn:
        cur = conn.cursor()

        # Core reference data: menu items and employees
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff'
            )
            """
        )

        # Active employees for a given day (for daily rotation)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS active_employees (
                employee_id TEXT PRIMARY KEY,
                active_date TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
            """
        )

        # Inventory: current stock and availability per item
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                item_id INTEGER PRIMARY KEY,
                stock_qty INTEGER NOT NULL DEFAULT 0,
                is_available INTEGER NOT NULL DEFAULT 1,
                reorder_level INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
            """
        )

        # Tables in the restaurant
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                seats INTEGER NOT NULL DEFAULT 4,
                status TEXT NOT NULL DEFAULT 'available'  -- available, occupied, reserved, out_of_service
            )
            """
        )

        # Orders and order line items
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                table_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending', -- pending, paid, cancelled
                total REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (table_id) REFERENCES tables(id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
            """
        )

        # Inventory change logs for owner visibility
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                item_id INTEGER NOT NULL,
                old_qty INTEGER,
                new_qty INTEGER,
                change_type TEXT NOT NULL, -- manual_adjustment, sale, refund, correction
                reason TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
            """
        )

        # Basic seeding from existing config.py, if tables are empty.
        from config import MENU_ITEMS, EMPLOYEES

        # Seed items
        cur.execute("SELECT COUNT(*) AS c FROM items")
        if cur.fetchone()["c"] == 0:
            for item in MENU_ITEMS:
                cur.execute(
                    """
                    INSERT INTO items (id, name, price, category, is_active)
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (item["id"], item["name"], item["price"], item["category"]),
                )
                # Initialize inventory entries with stock 0 and available
                cur.execute(
                    """
                    INSERT OR IGNORE INTO inventory (item_id, stock_qty, is_available, reorder_level)
                    VALUES (?, 0, 1, 0)
                    """,
                    (item["id"],),
                )

        # Seed employees
        cur.execute("SELECT COUNT(*) AS c FROM employees")
        if cur.fetchone()["c"] == 0:
            for emp_id, data in EMPLOYEES.items():
                cur.execute(
                    """
                    INSERT INTO employees (id, name, position, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (emp_id, data["name"], data["position"], "staff"),
                )


def get_all_menu_items():
    """Return ALL active items with current stock/availability (for management view)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT i.id, i.name, i.price, i.category,
                   COALESCE(inv.stock_qty, 0) AS stock_qty,
                   COALESCE(inv.is_available, 1) AS is_available
            FROM items i
            LEFT JOIN inventory inv ON inv.item_id = i.id
            WHERE i.is_active = 1
            ORDER BY i.category, i.name
            """
        )
        return cur.fetchall()


def get_available_menu_items():
    """Return list of available items with current stock."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT i.id, i.name, i.price, i.category,
                   inv.stock_qty, inv.is_available
            FROM items i
            LEFT JOIN inventory inv ON inv.item_id = i.id
            WHERE i.is_active = 1
              AND (inv.is_available = 1 OR inv.is_available IS NULL)
              AND (inv.stock_qty IS NULL OR inv.stock_qty > 0)
            ORDER BY i.category, i.name
            """
        )
        return cur.fetchall()


def get_all_employees():
    """Return all employees."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, position, role
            FROM employees
            ORDER BY name
            """
        )
        return cur.fetchall()


def get_active_employees_for_today():
    """Return employees marked active for today (by manager)."""
    from datetime import date

    today = date.today().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT e.id, e.name, e.position, e.role
            FROM employees e
            JOIN active_employees a ON a.employee_id = e.id
            WHERE a.active_date = ?
            ORDER BY e.name
            """,
            (today,),
        )
        return cur.fetchall()


def set_active_employees_for_today(employee_ids):
    """Replace today's active employees with the given list of IDs."""
    from datetime import date

    today = date.today().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        # Clear existing records for today
        cur.execute("DELETE FROM active_employees WHERE active_date = ?", (today,))

        for emp_id in employee_ids:
            cur.execute(
                """
                INSERT OR REPLACE INTO active_employees (employee_id, active_date)
                VALUES (?, ?)
                """,
                (emp_id, today),
            )


def update_inventory(item_id: int, new_qty: int, employee_id: str | None = None, reason: str | None = None):
    """Set inventory quantity for an item and log the change."""
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT stock_qty FROM inventory WHERE item_id = ?", (item_id,))
        row = cur.fetchone()
        old_qty = row["stock_qty"] if row else 0

        cur.execute(
            """
            INSERT INTO inventory (item_id, stock_qty, is_available, reorder_level)
            VALUES (?, ?, 1, 0)
            ON CONFLICT(item_id) DO UPDATE SET stock_qty = excluded.stock_qty
            """,
            (item_id, new_qty),
        )

        cur.execute(
            """
            INSERT INTO inventory_logs
                (employee_id, item_id, old_qty, new_qty, change_type, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id,
                item_id,
                old_qty,
                new_qty,
                "manual_adjustment",
                reason,
                datetime.utcnow().isoformat(),
            ),
        )


def set_item_availability(item_id: int, is_available: bool, employee_id: str | None = None, reason: str | None = None):
    """Toggle whether an item is available for sale and log if needed."""
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT stock_qty, is_available FROM inventory WHERE item_id = ?", (item_id,))
        row = cur.fetchone()
        stock_qty = row["stock_qty"] if row else 0
        old_available = row["is_available"] if row else 1

        cur.execute(
            """
            INSERT INTO inventory (item_id, stock_qty, is_available, reorder_level)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(item_id) DO UPDATE SET is_available = excluded.is_available
            """,
            (item_id, stock_qty, 1 if is_available else 0),
        )

        if old_available != (1 if is_available else 0):
            cur.execute(
                """
                INSERT INTO inventory_logs
                    (employee_id, item_id, old_qty, new_qty, change_type, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    employee_id,
                    item_id,
                    stock_qty,
                    stock_qty,
                    "availability_change",
                    reason,
                    datetime.utcnow().isoformat(),
                ),
            )


def get_tables():
    """Return all tables with their current status."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, seats, status
            FROM tables
            ORDER BY id
            """
        )
        return cur.fetchall()


def update_table_status(table_id: int, status: str):
    """Update a table's status (available, occupied, reserved, out_of_service)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tables SET status = ? WHERE id = ?",
            (status, table_id),
        )


def create_order(employee_id: str, employee_name: str, table_id: int | None, items):
    """
    Create an order and its line items.

    `items` should be an iterable of (MenuItem, quantity) or
    objects with .item_id, .name, .price attributes.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # Calculate total from provided items
        total = sum(m.price * qty for m, qty in items)

        cur.execute(
            """
            INSERT INTO orders (employee_id, employee_name, table_id, status, total, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id,
                employee_name,
                table_id,
                "pending",
                total,
                datetime.utcnow().isoformat(),
            ),
        )
        order_id = cur.lastrowid

        for menu_item, qty in items:
            line_total = menu_item.price * qty
            cur.execute(
                """
                INSERT INTO order_items
                    (order_id, item_id, item_name, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    menu_item.item_id,
                    menu_item.name,
                    qty,
                    menu_item.price,
                    line_total,
                ),
            )

            # Reduce inventory and log as sale
            cur.execute(
                "SELECT stock_qty FROM inventory WHERE item_id = ?",
                (menu_item.item_id,),
            )
            row = cur.fetchone()
            old_qty = row["stock_qty"] if row else 0
            new_qty = max(0, old_qty - qty)

            cur.execute(
                """
                INSERT INTO inventory (item_id, stock_qty, is_available, reorder_level)
                VALUES (?, ?, 1, 0)
                ON CONFLICT(item_id) DO UPDATE SET stock_qty = ?
                """,
                (menu_item.item_id, new_qty, new_qty),
            )

            cur.execute(
                """
                INSERT INTO inventory_logs
                    (employee_id, item_id, old_qty, new_qty, change_type, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    employee_id,
                    menu_item.item_id,
                    old_qty,
                    new_qty,
                    "sale",
                    f"Order {order_id}",
                    datetime.utcnow().isoformat(),
                ),
            )

        return order_id


def mark_order_paid(order_id: int):
    """Mark an order as paid."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE orders SET status = 'paid' WHERE id = ?",
            (order_id,),
        )


def create_item(name: str, price: float, category: str, stock_qty: int = 0,
                employee_id: str | None = None, reason: str | None = None) -> int:
    """
    Create a new menu item with an auto-generated ID and optional initial stock.

    Returns the new item ID.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # Insert into items; let SQLite auto-generate the ID.
        cur.execute(
            """
            INSERT INTO items (name, price, category, is_active)
            VALUES (?, ?, ?, ?)
            """,
            (name, price, category, 1),
        )
        item_id = cur.lastrowid

        # Initialize inventory entry
        cur.execute(
            """
            INSERT INTO inventory (item_id, stock_qty, is_available, reorder_level)
            VALUES (?, ?, ?, ?)
            """,
            (item_id, max(0, stock_qty), 1, 0),
        )

        # Log initial stock if any
        cur.execute(
            """
            INSERT INTO inventory_logs
                (employee_id, item_id, old_qty, new_qty, change_type, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id,
                item_id,
                0,
                max(0, stock_qty),
                "manual_adjustment",
                reason or "Initial stock",
                datetime.utcnow().isoformat(),
            ),
        )

        return item_id


