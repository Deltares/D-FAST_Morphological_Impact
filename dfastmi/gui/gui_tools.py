from PyQt5.QtWidgets import QLayoutItem

def clear_layout_item(item: QLayoutItem):
    """Recursively removes all widgets in this layout item.

    Parameters
    ----------
    item : The layout item
    """
    if not item:
        return
    
    widget = item.widget()
    if widget:
        widget.setParent(None)
        widget.deleteLater()
        return

    layout = item.layout()
    if layout:
        while layout.count():
            layout_item = layout.takeAt(0)
            clear_layout_item(layout_item)