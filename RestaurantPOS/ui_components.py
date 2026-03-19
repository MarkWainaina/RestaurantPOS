# UI components and window management
import tkinter as tk
from tkinter import ttk, messagebox
from models import MenuItem, Order
from styles import *
from config import PAYMENT_METHODS
from data_handler import save_order, load_order_history


class MenuDisplay:
    """Handles menu items display"""
    def __init__(self, parent, menu_items, add_callback):
        self.parent = parent
        self.menu_items = menu_items
        self.add_callback = add_callback
        
        # Create frame
        menu_label = tk.Label(self.parent, text="Menu Items:", 
                             font=FONT_HEADER, bg=COLOR_WHITE)
        menu_label.pack(padx=PADDING_LARGE, pady=(15, 5), anchor=tk.W)
        
        menu_frame_outer = tk.Frame(self.parent, bg=COLOR_WHITE)
        menu_frame_outer.pack(padx=PADDING_LARGE, pady=PADDING_MEDIUM, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(menu_frame_outer)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.menu_canvas = tk.Canvas(menu_frame_outer, bg=COLOR_WHITE, highlightthickness=0,
                                     yscrollcommand=scrollbar.set)
        self.menu_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.menu_canvas.yview)
        
        self.menu_frame = tk.Frame(self.menu_canvas, bg=COLOR_WHITE)
        self.menu_window = self.menu_canvas.create_window((0, 0), window=self.menu_frame, anchor=tk.NW)
        
        self.display()
    
    def display(self):
        """Display menu items"""
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        
        current_category = None
        for item in self.menu_items:
            if item.category != current_category:
                current_category = item.category
                category_label = tk.Label(self.menu_frame, text=current_category, 
                                         font=FONT_HEADER, bg=COLOR_LIGHT_GRAY, fg=COLOR_DARK_TEXT)
                category_label.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=(10, 5))
            
            item_frame = tk.Frame(self.menu_frame, bg=COLOR_WHITE, relief=tk.FLAT, bd=0)
            item_frame.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_SMALL)
            
            item_info = tk.Label(item_frame, text=f"{item.name} - ${item.price:.2f}", 
                                font=FONT_LABEL, bg=COLOR_WHITE, justify=tk.LEFT)
            item_info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
            
            qty_var = tk.StringVar(value="1")
            qty_spinbox = ttk.Spinbox(item_frame, from_=1, to=99, textvariable=qty_var, width=3)
            qty_spinbox.pack(side=tk.LEFT, padx=PADDING_MEDIUM)
            
            add_btn = tk.Button(item_frame, text="Add", width=6,
                               command=lambda i=item, q=qty_var: self.add_callback(i, q),
                               bg=COLOR_INFO, fg=COLOR_WHITE, font=FONT_SMALL)
            add_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        self.menu_frame.update_idletasks()
        self.menu_canvas.config(scrollregion=self.menu_canvas.bbox("all"))


class OrderDisplay:
    """Handles order items display"""
    def __init__(self, parent, remove_callback):
        self.parent = parent
        self.remove_callback = remove_callback
        self.current_order = None
        
        order_label = tk.Label(self.parent, text="Current Order:", 
                              font=FONT_HEADER, bg=COLOR_WHITE)
        order_label.pack(padx=PADDING_LARGE, pady=(10, 5), anchor=tk.W)
        
        order_frame_outer = tk.Frame(self.parent, bg=COLOR_WHITE)
        order_frame_outer.pack(padx=PADDING_LARGE, pady=PADDING_MEDIUM, fill=tk.BOTH, expand=True)
        
        scrollbar_order = ttk.Scrollbar(order_frame_outer)
        scrollbar_order.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.order_canvas = tk.Canvas(order_frame_outer, bg=COLOR_WHITE, highlightthickness=0,
                                      yscrollcommand=scrollbar_order.set)
        self.order_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_order.config(command=self.order_canvas.yview)
        
        self.order_frame = tk.Frame(self.order_canvas, bg=COLOR_WHITE)
        self.order_window = self.order_canvas.create_window((0, 0), window=self.order_frame, anchor=tk.NW)
    
    def update(self, order):
        """Update order display"""
        self.current_order = order
        
        for widget in self.order_frame.winfo_children():
            widget.destroy()
        
        if not self.current_order or not self.current_order.items:
            empty_label = tk.Label(self.order_frame, text="No items in order", 
                                  font=FONT_LABEL, bg=COLOR_WHITE, fg=COLOR_LIGHT_TEXT)
            empty_label.pack(padx=PADDING_LARGE, pady=20)
        else:
            for idx, (item, qty) in enumerate(self.current_order.items):
                item_total = item.price * qty
                item_frame = tk.Frame(self.order_frame, bg=COLOR_LIGHT_GRAY, relief=tk.FLAT, bd=0)
                item_frame.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_SMALL)
                
                item_info = tk.Label(item_frame, 
                                    text=f"{item.name} x{qty} = ${item_total:.2f}",
                                    font=FONT_LABEL, bg=COLOR_LIGHT_GRAY, justify=tk.LEFT)
                item_info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
                
                remove_btn = tk.Button(item_frame, text="Remove", width=8,
                                      command=lambda i=idx: self.remove_callback(i),
                                      bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_SMALL)
                remove_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        self.order_frame.update_idletasks()
        self.order_canvas.config(scrollregion=self.order_canvas.bbox("all"))


class OrderSummary:
    """Handles order summary display"""
    def __init__(self, parent):
        summary_frame = tk.Frame(parent, bg=COLOR_WHITE, relief=tk.RIDGE, bd=1)
        summary_frame.pack(padx=PADDING_LARGE, pady=PADDING_LARGE, fill=tk.X)
        
        tk.Label(summary_frame, text="Subtotal:", font=FONT_LABEL, bg=COLOR_WHITE).pack(anchor=tk.W, padx=PADDING_MEDIUM, pady=2)
        self.subtotal_label = tk.Label(summary_frame, text="$0.00", font=FONT_SUMMARY, bg=COLOR_WHITE, fg=COLOR_SUCCESS)
        self.subtotal_label.pack(anchor=tk.W, padx=PADDING_MEDIUM)
        
        tk.Label(summary_frame, text="Tax (10%):", font=FONT_LABEL, bg=COLOR_WHITE).pack(anchor=tk.W, padx=PADDING_MEDIUM, pady=(5, 2))
        self.tax_label = tk.Label(summary_frame, text="$0.00", font=FONT_SUMMARY, bg=COLOR_WHITE, fg=COLOR_DANGER)
        self.tax_label.pack(anchor=tk.W, padx=PADDING_MEDIUM)
        
        tk.Label(summary_frame, text="Total:", font=FONT_HEADER, bg=COLOR_WHITE).pack(anchor=tk.W, padx=PADDING_MEDIUM, pady=(5, 2))
        self.total_label = tk.Label(summary_frame, text="$0.00", font=FONT_TOTAL, bg=COLOR_WHITE, fg=COLOR_PRIMARY)
        self.total_label.pack(anchor=tk.W, padx=PADDING_MEDIUM, pady=(0, 5))
    
    def update(self, order):
        """Update summary display"""
        from styles import TAX_RATE
        
        if not order or not order.items:
            self.subtotal_label.config(text="$0.00")
            self.tax_label.config(text="$0.00")
            self.total_label.config(text="$0.00")
        else:
            subtotal = order.get_total()
            tax = subtotal * TAX_RATE
            total = subtotal + tax
            
            self.subtotal_label.config(text=f"${subtotal:.2f}")
            self.tax_label.config(text=f"${tax:.2f}")
            self.total_label.config(text=f"${total:.2f}")


class PaymentWindow:
    """Handles payment processing window"""
    def __init__(self, parent, order, callback):
        self.order = order
        self.callback = callback
        
        payment_window = tk.Toplevel(parent)
        payment_window.title("Payment")
        payment_window.geometry(f"{PAYMENT_WINDOW_WIDTH}x{PAYMENT_WINDOW_HEIGHT}")
        payment_window.config(bg=COLOR_WHITE)
        
        # Order summary
        summary_text = "ORDER SUMMARY\n" + "="*40 + "\n\n"
        for item_name, qty, item_total in order.get_itemized():
            summary_text += f"{item_name} x{qty}: ${item_total:.2f}\n"
        
        from styles import TAX_RATE
        subtotal = order.get_total()
        tax = subtotal * TAX_RATE
        total = subtotal + tax
        
        summary_text += "\n" + "-"*40 + "\n"
        summary_text += f"Subtotal: ${subtotal:.2f}\n"
        summary_text += f"Tax ({int(TAX_RATE*100)}%): ${tax:.2f}\n"
        summary_text += f"Total: ${total:.2f}\n"
        
        summary_label = tk.Label(payment_window, text=summary_text, font=FONT_MONOSPACE,
                                bg=COLOR_WHITE, justify=tk.LEFT)
        summary_label.pack(padx=PADDING_LARGE, pady=15)
        
        # Payment method
        self.payment_method = tk.StringVar(value="Cash")
        
        method_frame = tk.Frame(payment_window, bg=COLOR_WHITE)
        method_frame.pack(fill=tk.X, padx=PADDING_LARGE, pady=PADDING_LARGE)
        
        tk.Label(method_frame, text="Payment Method:", font=FONT_HEADER, bg=COLOR_WHITE).pack(anchor=tk.W)
        
        for method in PAYMENT_METHODS:
            tk.Radiobutton(method_frame, text=method, variable=self.payment_method, value=method,
                          bg=COLOR_WHITE, font=FONT_LABEL).pack(anchor=tk.W)
        
        # Buttons
        button_frame = tk.Frame(payment_window, bg=COLOR_WHITE)
        button_frame.pack(fill=tk.X, padx=PADDING_LARGE, pady=15)
        
        tk.Button(button_frame, text="Confirm Payment", command=lambda: self.confirm(callback, payment_window, total),
                 bg=COLOR_SUCCESS, fg=COLOR_WHITE, font=FONT_HEADER, width=20).pack(pady=5)
        tk.Button(button_frame, text="Cancel", command=payment_window.destroy,
                 bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_LABEL, width=20).pack(pady=5)
    
    def confirm(self, callback, window, total):
        """Confirm payment"""
        self.order.status = "completed"
        save_order(self.order, self.payment_method.get())
        
        messagebox.showinfo("Success", 
                          f"Payment processed!\nEmployee: {self.order.employee_name}\nTotal: ${total:.2f}")
        
        callback()
        window.destroy()


class HistoryWindow:
    """Handles order history display"""
    def __init__(self, parent):
        history_window = tk.Toplevel(parent)
        history_window.title("Order History")
        history_window.geometry(f"{HISTORY_WINDOW_WIDTH}x{HISTORY_WINDOW_HEIGHT}")
        history_window.config(bg=COLOR_WHITE)
        
        orders = load_order_history()
        
        if not orders:
            tk.Label(history_window, text="No orders yet", font=FONT_HEADER,
                    bg=COLOR_WHITE).pack(pady=20)
            return
        
        # Create text widget with scrollbar
        text_frame = tk.Frame(history_window, bg=COLOR_WHITE)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING_LARGE, pady=PADDING_LARGE)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, font=FONT_MONOSPACE,
                             bg=COLOR_WHITE, relief=tk.SUNKEN, bd=1)
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
