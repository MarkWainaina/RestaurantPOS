# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os

from styles import *
from database import (
    initialize_database,
    get_all_menu_items,
    update_inventory,
    set_item_availability,
    create_item,
    get_all_employees,
    get_active_employees_for_today,
    set_active_employees_for_today,
)


initialize_database()


class ManagementApp:
    """Simple management app for staff to handle inventory."""

    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.title("Restaurant Management")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.config(bg=COLOR_BACKGROUND)

        self.items = []
        self.selected_item_id = None

        self.build_ui()
        self.load_items()

    def build_ui(self):
        header = tk.Frame(self.root, bg=COLOR_HEADER, height=60)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="🍽️ Management",
            font=FONT_TITLE,
            bg=COLOR_HEADER,
            fg=COLOR_WHITE,
        )
        title.pack(pady=PADDING_LARGE)

        content = tk.Frame(self.root, bg=COLOR_BACKGROUND)
        content.pack(fill=tk.BOTH, expand=True, padx=PADDING_LARGE, pady=PADDING_LARGE)

        left = tk.Frame(content, bg=COLOR_WHITE, relief=tk.SUNKEN, bd=1)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right = tk.Frame(content, bg=COLOR_WHITE, relief=tk.SUNKEN, bd=1)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # Items list
        columns = ("id", "name", "category", "price", "stock", "available")
        self.tree = ttk.Treeview(
            left,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("category", text="Category")
        self.tree.heading("price", text="Price")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("available", text="Available")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("name", width=160)
        self.tree.column("category", width=80)
        self.tree.column("price", width=70, anchor=tk.E)
        self.tree.column("stock", width=70, anchor=tk.CENTER)
        self.tree.column("available", width=80, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_LARGE, pady=PADDING_LARGE)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_item)

        # Actions
        actions_label = tk.Label(
            right,
            text="Actions",
            font=FONT_HEADER,
            bg=COLOR_WHITE,
        )
        actions_label.pack(padx=PADDING_LARGE, pady=(PADDING_LARGE, PADDING_MEDIUM))

        btn_add = tk.Button(
            right,
            text="Add New Item",
            font=FONT_LABEL,
            bg=COLOR_SUCCESS,
            fg=COLOR_WHITE,
            width=18,
            command=self.add_item,
        )
        btn_add.pack(pady=5)

        btn_inc = tk.Button(
            right,
            text="Increase Stock",
            font=FONT_LABEL,
            bg=COLOR_SUCCESS,
            fg=COLOR_WHITE,
            width=18,
            command=self.increase_stock,
        )
        btn_inc.pack(pady=5)

        btn_dec = tk.Button(
            right,
            text="Decrease Stock",
            font=FONT_LABEL,
            bg=COLOR_DANGER,
            fg=COLOR_WHITE,
            width=18,
            command=self.decrease_stock,
        )
        btn_dec.pack(pady=5)

        btn_toggle = tk.Button(
            right,
            text="Toggle Availability",
            font=FONT_LABEL,
            bg=COLOR_INFO,
            fg=COLOR_WHITE,
            width=18,
            command=self.toggle_availability,
        )
        btn_toggle.pack(pady=5)

        btn_refresh = tk.Button(
            right,
            text="Refresh",
            font=FONT_LABEL,
            bg=COLOR_HEADER,
            fg=COLOR_WHITE,
            width=18,
            command=self.load_items,
        )
        btn_refresh.pack(pady=5)

        btn_reports = tk.Button(
            right,
            text="View Sales Reports",
            font=FONT_LABEL,
            bg=COLOR_INFO,
            fg=COLOR_WHITE,
            width=18,
            command=self.view_reports,
        )
        btn_reports.pack(pady=5)

        btn_manage_staff = tk.Button(
            right,
            text="Manage Today's Staff",
            font=FONT_LABEL,
            bg=COLOR_SUCCESS,
            fg=COLOR_WHITE,
            width=18,
            command=self.manage_staff,
        )
        btn_manage_staff.pack(pady=5)

    def load_items(self):
        """Load items from the database into the table."""
        # Clear current rows
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        self.items = list(get_all_menu_items())
        for row in self.items:
            item_id = row["id"]
            name = row["name"]
            category = row["category"]
            price = row["price"]
            stock = row["stock_qty"] if row["stock_qty"] is not None else 0
            available = "Yes" if row["is_available"] else "No"
            self.tree.insert(
                "",
                tk.END,
                iid=str(item_id),
                values=(item_id, name, category, f"{price:.2f}", stock, available),
            )

        self.selected_item_id = None

    def on_select_item(self, event=None):
        selected = self.tree.selection()
        if not selected:
            self.selected_item_id = None
            return
        self.selected_item_id = int(selected[0])

    def require_selection(self):
        if self.selected_item_id is None:
            messagebox.showwarning("No item selected", "Please select an item first.")
            return False
        return True

    def ask_quantity_change(self, title):
        try:
            value = simpledialog.askinteger(
                title,
                "Enter quantity:",
                minvalue=1,
                parent=self.root,
            )
        except Exception:
            return None
        return value

    def get_current_stock(self, item_id):
        for row in self.items:
            if row["id"] == item_id:
                return row["stock_qty"] if row["stock_qty"] is not None else 0
        return 0

    def add_item(self):
        """Prompt for a new item and save it to the database."""
        name = simpledialog.askstring("New Item", "Enter item name:", parent=self.root)
        if not name:
            return

        category = simpledialog.askstring(
            "New Item", "Enter category (e.g. Food, Drink):", parent=self.root
        )
        if not category:
            return

        try:
            price = simpledialog.askfloat(
                "New Item", "Enter price:", minvalue=0.0, parent=self.root
            )
        except Exception:
            price = None
        if price is None:
            return

        try:
            stock = simpledialog.askinteger(
                "New Item", "Initial stock quantity:", minvalue=0, parent=self.root
            )
        except Exception:
            stock = None
        if stock is None:
            return

        # Create the item in the database with an auto-generated ID
        item_id = create_item(
            name=name,
            price=price,
            category=category,
            stock_qty=stock,
            employee_id=None,
            reason="Created from management app",
        )
        messagebox.showinfo("Success", f"Item '{name}' created with ID {item_id}.")
        self.load_items()

    def increase_stock(self):
        if not self.require_selection():
            return
        qty = self.ask_quantity_change("Increase Stock")
        if not qty:
            return
        current = self.get_current_stock(self.selected_item_id)
        new_qty = current + qty
        update_inventory(self.selected_item_id, new_qty, employee_id=None, reason="Manual increase")
        messagebox.showinfo("Success", f"Stock updated to {new_qty}.")
        self.load_items()

    def decrease_stock(self):
        if not self.require_selection():
            return
        qty = self.ask_quantity_change("Decrease Stock")
        if not qty:
            return
        current = self.get_current_stock(self.selected_item_id)
        new_qty = max(0, current - qty)
        update_inventory(self.selected_item_id, new_qty, employee_id=None, reason="Manual decrease")
        messagebox.showinfo("Success", f"Stock updated to {new_qty}.")
        self.load_items()

    def toggle_availability(self):
        if not self.require_selection():
            return
        # Find current availability
        current_available = True
        for row in self.items:
            if row["id"] == self.selected_item_id:
                current_available = bool(row["is_available"])
                break
        new_available = not current_available
        set_item_availability(
            self.selected_item_id,
            new_available,
            employee_id=None,
            reason="Manual toggle",
        )
        status = "available" if new_available else "unavailable"
        messagebox.showinfo("Success", f"Item is now {status}.")
        self.load_items()

    def view_reports(self):
        """Show sales reports from POS orders_history.json."""
        orders_file = "orders_history.json"
        if not os.path.exists(orders_file):
            messagebox.showinfo("No data", "No orders history found yet.")
            return

        try:
            with open(orders_file, "r", encoding="utf-8") as f:
                orders = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read orders history:\n{e}")
            return

        report_win = tk.Toplevel(self.root)
        report_win.title("Sales Reports")
        report_win.geometry("800x500")
        report_win.config(bg=COLOR_WHITE)

        columns = ("item", "quantity", "waiter", "method", "amount", "timestamp")
        tree_frame = tk.Frame(report_win)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                            yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)

        tree.heading("item", text="Item Sold")
        tree.heading("quantity", text="Quantity")
        tree.heading("waiter", text="Waiter")
        tree.heading("method", text="Payment Method")
        tree.heading("amount", text="Amount Paid")
        tree.heading("timestamp", text="Timestamp")

        tree.column("item", width=180)
        tree.column("quantity", width=70, anchor=tk.CENTER)
        tree.column("waiter", width=140)
        tree.column("method", width=100)
        tree.column("amount", width=100, anchor=tk.E)
        tree.column("timestamp", width=180)

        tree.pack(fill=tk.BOTH, expand=True)

        for order in orders:
            waiter = order.get("employee_name", "")
            method = order.get("payment_method", "")
            timestamp = order.get("timestamp", "")

            # Determine amount paid from payment_info if available
            payment_info = order.get("payment_info", {})
            amount_paid = None
            if method == "Cash" and "cash_paid" in payment_info:
                amount_paid = float(payment_info["cash_paid"])
            elif method == "M-Pesa":
                # For M-Pesa, assume full total was paid
                amount_paid = float(order.get("total", 0))
            else:
                amount_paid = float(order.get("total", 0))

            items = order.get("items", [])
            for item_name, qty in items:
                tree.insert(
                    "",
                    tk.END,
                    values=(
                        item_name,
                        qty,
                        waiter,
                        method,
                        f"{amount_paid:.2f}",
                        timestamp,
                    ),
                )

    def manage_staff(self):
        """Allow manager to choose which employees are active today."""
        # Fetch all employees and today's active employees
        all_emps = list(get_all_employees())
        active_today = {row["id"] for row in get_active_employees_for_today()}

        win = tk.Toplevel(self.root)
        win.title("Manage Today's Staff")
        win.geometry("600x400")
        win.config(bg=COLOR_WHITE)

        columns = ("id", "name", "position", "active")
        tree_frame = tk.Frame(win)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                            selectmode="browse", yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)

        tree.heading("id", text="ID")
        tree.heading("name", text="Name")
        tree.heading("position", text="Position")
        tree.heading("active", text="On Duty Today")

        tree.column("id", width=80, anchor=tk.CENTER)
        tree.column("name", width=180)
        tree.column("position", width=140)
        tree.column("active", width=100, anchor=tk.CENTER)

        tree.pack(fill=tk.BOTH, expand=True)

        # Track active state in a dict
        active_map = {}
        for emp in all_emps:
            emp_id = emp["id"]
            is_active = emp_id in active_today
            active_map[emp_id] = is_active
            tree.insert(
                "",
                tk.END,
                iid=emp_id,
                values=(
                    emp_id,
                    emp["name"],
                    emp["position"],
                    "Yes" if is_active else "No",
                ),
            )

        def toggle_active(event=None):
            item_id = tree.focus()
            if not item_id:
                return
            emp_id = item_id
            current = active_map.get(emp_id, False)
            new_val = not current
            active_map[emp_id] = new_val
            tree.set(item_id, "active", "Yes" if new_val else "No")

        tree.bind("<Double-1>", toggle_active)

        def save_staff():
            selected_ids = [emp_id for emp_id, active in active_map.items() if active]
            set_active_employees_for_today(selected_ids)
            messagebox.showinfo("Saved", "Today's active staff has been updated.")
            win.destroy()

        btn_frame = tk.Frame(win, bg=COLOR_WHITE)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(
            btn_frame,
            text="Save",
            command=save_staff,
            bg=COLOR_SUCCESS,
            fg=COLOR_WHITE,
            font=FONT_LABEL,
            width=10,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Close",
            command=win.destroy,
            bg=COLOR_DANGER,
            fg=COLOR_WHITE,
            font=FONT_LABEL,
            width=10,
        ).pack(side=tk.LEFT, padx=5)


if __name__ == "__main__":
    app = ManagementApp()
    app.root.mainloop()

