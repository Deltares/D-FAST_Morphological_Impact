from PyQt5.QtWidgets import QLayout, QLayoutItem, QWidget

def clear_layout_item(item: QLayoutItem):
    """Recursively removes all widgets in this layout item object.

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
    """Recursively removes all widgets from this layout object.

    Parameters
    ----------
    layout : QLayout
        The layout object.
    """
    while layout.count():
        layout_item = layout.takeAt(0)
        clear_layout_item(layout_item)

def remove_widget(widget: QWidget):
    """Remove this widget.
    Widget can be removed when relation to parent is broken.  

    Parameters
    ----------
    widget : QWidget
        The widget object. 
    """
    widget.setParent(None)
    widget.deleteLater()