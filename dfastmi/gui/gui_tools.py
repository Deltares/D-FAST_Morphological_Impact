from PyQt5.QtWidgets import QLayout, QLayoutItem, QWidget

def clear_layout_item(item: QLayoutItem):
    """Recursively remove all widgets in the provided layout item object.

    Parameters
    ----------
    item : The layout item object.
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
    """Recursively remove all widgets from the provided layout object.

    Parameters
    ----------
    layout : QLayout
        The layout object.
    """
    while layout.count():
        layout_item = layout.takeAt(0)
        clear_layout_item(layout_item)

def remove_widget(widget: QWidget):
    """Remove the provided widget.
    Widget is scheduled for deletion by breaking relationship with parent.  

    Parameters
    ----------
    widget : QWidget
        The widget object. 
    """
    widget.setParent(None)