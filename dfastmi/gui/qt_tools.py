from PyQt5.QtWidgets import QLayout, QLayoutItem, QWidget

def clear_layout_item(item: QLayoutItem):
    """Recursively remove all widgets in the provided layout item object.

    If the managed item is a widget, it is removed from its parent layout.
    If the managed item is a layout, all widgets within that layout are removed.
    
    Parameters
    ----------
    item : QLayoutItem
        The layout item to be cleared.
    """
    if not item:
        return
    
    widget = item.widget()
    if widget:
        remove_widget(widget)
        return

    layout = item.layout()
    if layout:
        clear_layout(layout)

def clear_layout(layout: QLayout):
    """Recursively remove all widgets from the provided layout object, including from nested layouts.

    Parameters
    ----------
    layout : QLayout
        The layout object to be cleared.
    """
    while layout.count():
        layout_item = layout.takeAt(0)
        clear_layout_item(layout_item)

def remove_widget(widget: QWidget):
    """Remove the provided widget from its parent layout.
    Widget is scheduled for deletion by breaking relationship with parent.  

    Parameters
    ----------
    widget : QWidget
        The widget to be removed. 
    """
    widget.setParent(None)