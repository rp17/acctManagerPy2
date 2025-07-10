import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Optional
import math

class LayoutCache:
    """CRITICAL: Cache layout calculations for performance"""
    def __init__(self):
        self._dimension_cache = {}
        self._layout_cache = {}
    def get_widget_dimensions(self, widget: tk.Widget) -> Tuple[int, int]:
        widget_id = id(widget)
        if widget_id not in self._dimension_cache:
            widget.update_idletasks()
            self._dimension_cache[widget_id] = (widget.winfo_reqwidth(), widget.winfo_reqheight())
        return self._dimension_cache[widget_id]

class LayoutUtilities:
    @staticmethod
    def make_compact_grid(container: tk.Widget, rows: int, cols: int,
                         initial_x: int = 6, initial_y: int = 6,
                         x_pad: int = 6, y_pad: int = 6):
        """CRITICAL: Create compact grid layout with optimal spacing"""
        children = container.winfo_children()
        max_items = min(len(children), rows * cols)
        col_widths = LayoutUtilities._calculate_column_widths(children, rows, cols)
        for i in range(max_items):
            row = i // cols
            col = i % cols
            widget = children[i]
            x = initial_x + sum(col_widths[:col]) + (col * x_pad)
            y = initial_y + (row * (widget.winfo_reqheight() + y_pad))
            widget.place(x=x, y=y, width=col_widths[col])

    @staticmethod
    def _calculate_column_widths(widgets: List[tk.Widget], rows: int, cols: int) -> List[int]:
        """CRITICAL: Calculate optimal column widths for grid"""
        col_widths = [0] * cols
        for i, widget in enumerate(widgets):
            if i >= rows * cols:
                break
            col = i % cols
            widget.update_idletasks()
            width = widget.winfo_reqwidth()
            col_widths[col] = max(col_widths[col], width)
        return col_widths

    @staticmethod
    def make_uniform_grid(container: tk.Widget, rows: int, cols: int,
                         initial_x: int = 6, initial_y: int = 6,
                         x_pad: int = 6, y_pad: int = 6):
        """MANDATORY: Create uniform grid with equal cell sizes"""
        children = container.winfo_children()
        max_items = min(len(children), rows * cols)
        max_width = max_height = 0
        for widget in children[:max_items]:
            widget.update_idletasks()
            max_width = max(max_width, widget.winfo_reqwidth())
            max_height = max(max_height, widget.winfo_reqheight())
        for i in range(max_items):
            row = i // cols
            col = i % cols
            widget = children[i]
            x = initial_x + col * (max_width + x_pad)
            y = initial_y + row * (max_height + y_pad)
            widget.place(x=x, y=y, width=max_width, height=max_height)

    @staticmethod
    def create_form_layout(container: tk.Widget, label_widget_pairs: List[Tuple[tk.Widget, tk.Widget]],
                          padding: int = 5, label_width: int = 100):
        """CRITICAL: Create professional form layout with aligned labels"""
        for i, (label, widget) in enumerate(label_widget_pairs):
            widget.update_idletasks()
            y_pos = i * (widget.winfo_reqheight() + padding) + padding
            label.place(x=padding, y=y_pos, width=label_width)
            widget.place(x=padding + label_width + padding, y=y_pos,
                        width=container.winfo_width() - (padding * 3 + label_width))

    @staticmethod
    def print_widget_info(widget: tk.Widget):
        """CRITICAL: Debug widget dimensions and positioning"""
        widget.update_idletasks()
        print(f"Widget: {widget.__class__.__name__}")
        print(f"  Position: ({widget.winfo_x()}, {widget.winfo_y()})")
        print(f"  Size: {widget.winfo_width()}x{widget.winfo_height()}")
        print(f"  Required: {widget.winfo_reqwidth()}x{widget.winfo_reqheight()}")
        print()

    @staticmethod
    def highlight_widget_bounds(widget: tk.Widget, color: str = "red"):
        """MANDATORY: Visual debugging aid for widget positioning"""
        if isinstance(widget, (tk.Frame, tk.Label, tk.Entry, tk.Button)):
            widget.configure(highlightbackground=color, highlightthickness=2)
            widget.after(2000, lambda: widget.configure(highlightthickness=0))

    @staticmethod
    def validate_grid_layout(container: tk.Widget, expected_rows: int, expected_cols: int) -> bool:
        """CRITICAL: Validate grid layout correctness"""
        children = container.winfo_children()
        if len(children) != expected_rows * expected_cols:
            print(f"Warning: Expected {expected_rows * expected_cols} widgets, found {len(children)}")
            return False
        for i, widget in enumerate(children):
            row = i // expected_cols
            col = i % expected_cols
            expected_x = col * (widget.winfo_width() + 10)
            expected_y = row * (widget.winfo_height() + 10)
            if abs(widget.winfo_x() - expected_x) > 5:
                print(f"Warning: Widget {i} X position off by {abs(widget.winfo_x() - expected_x)}px")
                return False
        return True 