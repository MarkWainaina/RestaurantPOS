import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import json
import os

from database import (
    initialize_database,
    get_available_menu_items,
    create_order,
    mark_order_paid,
    get_active_employees_for_today,
)


initialize_database()


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
        """Calculate order total"""
        return sum(item.price * qty for item, qty in self.items)
    
    def get_itemized(self):
        """Return itemized breakdown"""
        return [(item.name, qty, item.price * qty) for item, qty in self.items]


class POSSystem:
    """Main POS System"""
    def __init__(self):
        self.menu = self.load_menu()
        self.employees = self.load_employees()
        self.orders_history = []
        self.current_order = None
        self.current_employee = None
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Restaurant POS System")
        self.root.geometry("900x700")
        self.root.config(bg="#f0f0f0")
        
        self.setup_ui()
    
    def load_menu(self):
        """Load menu items from the shared database."""
        db_items = get_available_menu_items()
        return [
            MenuItem(row["id"], row["name"], row["price"], row["category"])
            for row in db_items
        ]

    def refresh_menu(self):
        """Reload menu items from the database and update the UI."""
        self.menu = self.load_menu()
        self.display_menu()
    
    def load_employees(self):
        """Load employees marked active for today from the database."""
        rows = get_active_employees_for_today()
        employees = {
            row["id"]: {"name": row["name"], "position": row["position"]}
            for row in rows
        }
        return employees

    def refresh_employees(self):
        """Reload today's active employees and update the dropdown."""
        self.employees = self.load_employees()
        emp_options = [f"{eid}: {edata['name']}" for eid, edata in self.employees.items()]
        self.employee_combo["values"] = emp_options
        self.employee_var.set("")
        self.current_employee = None
    
    def setup_ui(self):
        """Setup the main UI"""
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        title_label = tk.Label(header_frame, text="🍽️ Restaurant POS System", 
                               font=("Arial", 18, "bold"), bg="#2c3e50", fg="white")
        title_label.pack(pady=10)
        
        # Main content frame
        content_frame = tk.Frame(self.root, bg="#f0f0f0")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Employee & Menu
        left_frame = tk.Frame(content_frame, bg="white", relief=tk.SUNKEN, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Employee Selection
        emp_label = tk.Label(left_frame, text="Select Employee:", 
                            font=("Arial", 10, "bold"), bg="white")
        emp_label.pack(padx=10, pady=(10, 5), anchor=tk.W)
        
        emp_frame = tk.Frame(left_frame, bg="white")
        emp_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.employee_var = tk.StringVar()
        emp_options = [f"{eid}: {edata['name']}" for eid, edata in self.employees.items()]
        
        self.employee_combo = ttk.Combobox(
            emp_frame,
            textvariable=self.employee_var,
            values=emp_options,
            state="readonly",
            width=28,
        )
        self.employee_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.employee_combo.bind("<<ComboboxSelected>>", self.select_employee)

        refresh_emp_btn = tk.Button(
            emp_frame,
            text="Refresh",
            command=self.refresh_employees,
            bg="#16a085",
            fg="white",
            font=("Arial", 8, "bold"),
            width=8,
        )
        refresh_emp_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Menu Items
        menu_label = tk.Label(left_frame, text="Menu Items:", 
                             font=("Arial", 10, "bold"), bg="white")
        menu_label.pack(padx=10, pady=(15, 5), anchor=tk.W)

        refresh_menu_btn = tk.Button(
            left_frame,
            text="Refresh Menu",
            command=self.refresh_menu,
            bg="#16a085",
            fg="white",
            font=("Arial", 8, "bold"),
            width=15,
        )
        refresh_menu_btn.pack(padx=10, pady=(0, 5), anchor=tk.W)
        
        # Create frame for menu items with scrollbar
        menu_frame_outer = tk.Frame(left_frame, bg="white")
        menu_frame_outer.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(menu_frame_outer)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.menu_canvas = tk.Canvas(menu_frame_outer, bg="white", highlightthickness=0,
                                     yscrollcommand=scrollbar.set)
        self.menu_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.menu_canvas.yview)
        
        self.menu_frame = tk.Frame(self.menu_canvas, bg="white")
        self.menu_window = self.menu_canvas.create_window((0, 0), window=self.menu_frame, anchor=tk.NW)
        
        self.display_menu()
        
        # Right side - Current Order
        right_frame = tk.Frame(content_frame, bg="white", relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        order_label = tk.Label(right_frame, text="Current Order:", 
                              font=("Arial", 10, "bold"), bg="white")
        order_label.pack(padx=10, pady=(10, 5), anchor=tk.W)
        
        # Order items display
        order_frame_outer = tk.Frame(right_frame, bg="white")
        order_frame_outer.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        scrollbar_order = ttk.Scrollbar(order_frame_outer)
        scrollbar_order.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.order_canvas = tk.Canvas(order_frame_outer, bg="white", highlightthickness=0,
                                      yscrollcommand=scrollbar_order.set)
        self.order_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_order.config(command=self.order_canvas.yview)
        
        self.order_frame = tk.Frame(self.order_canvas, bg="white")
        self.order_window = self.order_canvas.create_window((0, 0), window=self.order_frame, anchor=tk.NW)
        
        # Summary section
        summary_frame = tk.Frame(right_frame, bg="white", relief=tk.RIDGE, bd=1)
        summary_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Label(summary_frame, text="Subtotal:", font=("Arial", 9), bg="white").pack(anchor=tk.W, padx=5, pady=2)
        self.subtotal_label = tk.Label(summary_frame, text="$0.00", font=("Arial", 9, "bold"), bg="white", fg="#27ae60")
        self.subtotal_label.pack(anchor=tk.W, padx=5)
        
        tk.Label(summary_frame, text="Tax (10%):", font=("Arial", 9), bg="white").pack(anchor=tk.W, padx=5, pady=(5, 2))
        self.tax_label = tk.Label(summary_frame, text="$0.00", font=("Arial", 9, "bold"), bg="white", fg="#e74c3c")
        self.tax_label.pack(anchor=tk.W, padx=5)
        
        tk.Label(summary_frame, text="Total:", font=("Arial", 10, "bold"), bg="white").pack(anchor=tk.W, padx=5, pady=(5, 2))
        self.total_label = tk.Label(summary_frame, text="$0.00", font=("Arial", 12, "bold"), bg="white", fg="#2980b9")
        self.total_label.pack(anchor=tk.W, padx=5, pady=(0, 5))
        
        # Buttons frame
        button_frame = tk.Frame(right_frame, bg="white")
        button_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.clear_btn = tk.Button(button_frame, text="Clear Order", command=self.clear_order,
                                   bg="#e74c3c", fg="white", font=("Arial", 9), width=15)
        self.clear_btn.pack(pady=5)
        
        self.checkout_btn = tk.Button(button_frame, text="Proceed to Checkout", command=self.checkout,
                                      bg="#27ae60", fg="white", font=("Arial", 9, "bold"), width=15)
        self.checkout_btn.pack(pady=5)
        
        self.history_btn = tk.Button(button_frame, text="View Order History", command=self.view_history,
                                     bg="#3498db", fg="white", font=("Arial", 9), width=15)
        self.history_btn.pack(pady=5)
    
    def display_menu(self):
        """Display menu items"""
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        
        current_category = None
        for item in self.menu:
            if item.category != current_category:
                current_category = item.category
                category_label = tk.Label(self.menu_frame, text=current_category, 
                                         font=("Arial", 9, "bold"), bg="#ecf0f1", fg="#2c3e50")
                category_label.pack(fill=tk.X, padx=5, pady=(10, 5))
            
            item_frame = tk.Frame(self.menu_frame, bg="white", relief=tk.FLAT, bd=0)
            item_frame.pack(fill=tk.X, padx=5, pady=2)
            
            item_info = tk.Label(item_frame, text=f"{item.name} - ${item.price:.2f}", 
                                font=("Arial", 9), bg="white", justify=tk.LEFT)
            item_info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
            
            qty_var = tk.StringVar(value="1")
            qty_spinbox = ttk.Spinbox(item_frame, from_=1, to=99, textvariable=qty_var, width=3)
            qty_spinbox.pack(side=tk.LEFT, padx=5)
            
            add_btn = tk.Button(item_frame, text="Add", width=6,
                               command=lambda i=item, q=qty_var: self.add_to_order(i, q),
                               bg="#3498db", fg="white", font=("Arial", 8))
            add_btn.pack(side=tk.LEFT, padx=2)
        
        self.menu_frame.update_idletasks()
        self.menu_canvas.config(scrollregion=self.menu_canvas.bbox("all"))
    
    def select_employee(self, event=None):
        """Select employee for the order"""
        selection = self.employee_var.get()
        if selection:
            emp_id = selection.split(":")[0]
            emp_name = self.employees[emp_id]["name"]
            self.current_employee = (emp_id, emp_name)
            messagebox.showinfo("Success", f"Employee selected: {emp_name}")
    
    def add_to_order(self, menu_item, qty_var):
        """Add item to current order"""
        if not self.current_employee:
            messagebox.showwarning("Warning", "Please select an employee first!")
            return
        
        if not self.current_order:
            order_id = len(self.orders_history) + 1
            self.current_order = Order(order_id, self.current_employee[0], self.current_employee[1])
        
        quantity = int(qty_var.get())
        self.current_order.add_item(menu_item, quantity)
        self.update_order_display()
        messagebox.showinfo("Added", f"{menu_item.name} x{quantity} added to order!")
    
    def update_order_display(self):
        """Update the order display panel"""
        for widget in self.order_frame.winfo_children():
            widget.destroy()
        
        if not self.current_order or not self.current_order.items:
            empty_label = tk.Label(self.order_frame, text="No items in order", 
                                  font=("Arial", 10, "italic"), bg="white", fg="#95a5a6")
            empty_label.pack(padx=10, pady=20)
        else:
            for idx, (item, qty) in enumerate(self.current_order.items):
                item_total = item.price * qty
                item_frame = tk.Frame(self.order_frame, bg="#ecf0f1", relief=tk.FLAT, bd=0)
                item_frame.pack(fill=tk.X, padx=5, pady=3)
                
                item_info = tk.Label(item_frame, 
                                    text=f"{item.name} x{qty} = ${item_total:.2f}",
                                    font=("Arial", 9), bg="#ecf0f1", justify=tk.LEFT)
                item_info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
                
                remove_btn = tk.Button(item_frame, text="Remove", width=8,
                                      command=lambda i=idx: self.remove_from_order(i),
                                      bg="#e74c3c", fg="white", font=("Arial", 8))
                remove_btn.pack(side=tk.LEFT, padx=2)
        
        self.update_summary()
        self.order_frame.update_idletasks()
        self.order_canvas.config(scrollregion=self.order_canvas.bbox("all"))
    
    def remove_from_order(self, index):
        """Remove item from order"""
        if self.current_order:
            self.current_order.remove_item(index)
            self.update_order_display()
    
    def update_summary(self):
        """Update order summary"""
        if not self.current_order or not self.current_order.items:
            self.subtotal_label.config(text="$0.00")
            self.tax_label.config(text="$0.00")
            self.total_label.config(text="$0.00")
        else:
            subtotal = self.current_order.get_total()
            tax = subtotal * 0.10
            total = subtotal + tax
            
            self.subtotal_label.config(text=f"${subtotal:.2f}")
            self.tax_label.config(text=f"${tax:.2f}")
            self.total_label.config(text=f"${total:.2f}")
    
    def clear_order(self):
        """Clear current order"""
        if messagebox.askyesno("Confirm", "Clear the entire order?"):
            self.current_order = None
            self.update_order_display()
    
    def checkout(self):
        """Process payment and checkout"""
        if not self.current_order or not self.current_order.items:
            messagebox.showwarning("Warning", "Order is empty!")
            return
        
        subtotal = self.current_order.get_total()
        tax = subtotal * 0.10
        total = subtotal + tax
        
        # Payment window
        payment_window = tk.Toplevel(self.root)
        payment_window.title("Payment")
        payment_window.geometry("400x350")
        payment_window.config(bg="white")
        
        # Order summary
        summary_text = "ORDER SUMMARY\n" + "="*40 + "\n\n"
        for item_name, qty, item_total in self.current_order.get_itemized():
            summary_text += f"{item_name} x{qty}: ${item_total:.2f}\n"
        summary_text += "\n" + "-"*40 + "\n"
        summary_text += f"Subtotal: ${subtotal:.2f}\n"
        summary_text += f"Tax (10%): ${tax:.2f}\n"
        summary_text += f"Total: ${total:.2f}\n"
        
        summary_label = tk.Label(payment_window, text=summary_text, font=("Courier", 9),
                                bg="white", justify=tk.LEFT)
        summary_label.pack(padx=20, pady=15)

        # Served by (employee)
        served_frame = tk.Frame(payment_window, bg="white")
        served_frame.pack(fill=tk.X, padx=20, pady=(0, 5))
        tk.Label(
            served_frame,
            text=f"Served by: {self.current_order.employee_name}",
            font=("Arial", 9, "bold"),
            bg="white",
        ).pack(anchor=tk.W)

        # Payment method
        payment_method = tk.StringVar(value="M-Pesa")
        mpesa_number_var = tk.StringVar()
        cash_paid_var = tk.StringVar()
        
        method_frame = tk.Frame(payment_window, bg="white")
        method_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(method_frame, text="Payment Method:", font=("Arial", 9, "bold"), bg="white").pack(anchor=tk.W)

        # M-Pesa and Cash detail frames (hidden/shown based on selection)
        mpesa_frame = tk.Frame(payment_window, bg="white")
        tk.Label(mpesa_frame, text="M-Pesa Number:", font=("Arial", 9), bg="white").pack(anchor=tk.W)
        tk.Entry(mpesa_frame, textvariable=mpesa_number_var).pack(fill=tk.X)

        cash_frame = tk.Frame(payment_window, bg="white")
        tk.Label(cash_frame, text="Cash Paid (amount):", font=("Arial", 9), bg="white").pack(anchor=tk.W)
        tk.Entry(cash_frame, textvariable=cash_paid_var).pack(fill=tk.X)

        # Buttons frame (inputs will be shown just above this)
        button_frame = tk.Frame(payment_window, bg="white")
        button_frame.pack(fill=tk.X, padx=20, pady=15)

        def update_payment_fields(*args):
            # Hide both frames first
            mpesa_frame.pack_forget()
            cash_frame.pack_forget()
            method = payment_method.get()
            if method == "M-Pesa":
                mpesa_frame.pack(fill=tk.X, padx=20, pady=(5, 5), before=button_frame)
            elif method == "Cash":
                cash_frame.pack(fill=tk.X, padx=20, pady=(5, 10), before=button_frame)

        for method in ["M-Pesa", "Cash"]:
            tk.Radiobutton(
                method_frame,
                text=method,
                variable=payment_method,
                value=method,
                bg="white",
                font=("Arial", 9),
                command=update_payment_fields,
            ).pack(anchor=tk.W)

        # Initialize fields visibility based on default method
        update_payment_fields()
        
        def confirm_payment():
            method = payment_method.get()
            payment_info = {}

            if method == "M-Pesa":
                number = mpesa_number_var.get().strip()
                if not number:
                    messagebox.showwarning("Missing number", "Please enter the customer's M-Pesa number.")
                    return
                payment_info["mpesa_number"] = number
                # Here you would trigger an actual M-Pesa prompt/integration.

            elif method == "Cash":
                raw_amount = cash_paid_var.get().strip()
                try:
                    amount = float(raw_amount)
                except ValueError:
                    messagebox.showwarning("Invalid amount", "Please enter a valid cash amount.")
                    return
                if amount < total:
                    messagebox.showwarning("Insufficient cash", "Cash paid is less than total amount.")
                    return
                change = amount - total
                payment_info["cash_paid"] = amount
                payment_info["change"] = change

            self.current_order.status = "completed"
            self.orders_history.append(self.current_order)
            self.save_order(self.current_order, method, payment_info)
            
            served_by = self.current_order.employee_name
            info_lines = [
                "Payment processed!",
                f"Employee: {served_by}",
                f"Method: {method}",
                f"Total: ${total:.2f}",
            ]
            if method == "M-Pesa":
                info_lines.append(f"M-Pesa Number: {payment_info['mpesa_number']}")
            elif method == "Cash":
                info_lines.append(f"Cash Paid: ${payment_info['cash_paid']:.2f}")
                info_lines.append(f"Change: ${payment_info['change']:.2f}")

            messagebox.showinfo("Success", "\n".join(info_lines))
            
            self.current_order = None
            self.update_order_display()
            payment_window.destroy()
        
        tk.Button(button_frame, text="Confirm Payment", command=confirm_payment,
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold"), width=20).pack(pady=5)
        tk.Button(button_frame, text="Cancel", command=payment_window.destroy,
                 bg="#e74c3c", fg="white", font=("Arial", 10), width=20).pack(pady=5)
    
    def save_order(self, order, payment_method, payment_info=None):
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
        if payment_info:
            order_data["payment_info"] = payment_info
        
        # Create orders file if not exists
        orders_file = "orders_history.json"
        orders = []
        
        if os.path.exists(orders_file):
            with open(orders_file, "r") as f:
                orders = json.load(f)
        
        orders.append(order_data)
        
        with open(orders_file, "w") as f:
            json.dump(orders, f, indent=2)
    
    def view_history(self):
        """View order history"""
        history_window = tk.Toplevel(self.root)
        history_window.title("Order History")
        history_window.geometry("600x400")
        history_window.config(bg="white")
        
        if not os.path.exists("orders_history.json"):
            tk.Label(history_window, text="No orders yet", font=("Arial", 12),
                    bg="white").pack(pady=20)
            return
        
        with open("orders_history.json", "r") as f:
            orders = json.load(f)
        
        # Create text widget with scrollbar
        text_frame = tk.Frame(history_window, bg="white")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, font=("Courier", 9),
                             bg="white", relief=tk.SUNKEN, bd=1)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Display all orders
        for order in orders:
            text_widget.insert(tk.END, f"Order #{order['order_id']}\n")
            text_widget.insert(tk.END, f"Employee: {order['employee_name']} ({order['employee_id']})\n")
            text_widget.insert(tk.END, f"Time: {order['timestamp']}\n")
            text_widget.insert(tk.END, f"Payment: {order['payment_method']}\n")
            text_widget.insert(tk.END, "Items:\n")
            for item_name, qty in order['items']:
                text_widget.insert(tk.END, f"  - {item_name} x{qty}\n")
            text_widget.insert(tk.END, f"Total: ${order['total']:.2f}\n")
            text_widget.insert(tk.END, "-" * 50 + "\n\n")
        
        text_widget.config(state=tk.DISABLED)
    
    def run(self):
        """Start the POS system"""
        self.root.mainloop()


if __name__ == "__main__":
    pos_system = POSSystem()
    pos_system.run()
