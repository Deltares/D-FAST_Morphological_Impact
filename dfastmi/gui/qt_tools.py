# -*- coding: utf-8 -*-
"""
Copyright © 2024 Stichting Deltares.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation version 2.1.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, see <http://www.gnu.org/licenses/>.

contact: delft3d.support@deltares.nl
Stichting Deltares
P.O. Box 177
2600 MH Delft, The Netherlands

All indications and logos of, and references to, "Delft3D" and "Deltares"
are registered trademarks of Stichting Deltares, and remain the property of
Stichting Deltares. All rights reserved.

INFORMATION
This file is part of D-FAST Morphological Impact: https://github.com/Deltares/D-FAST_Morphological_Impact
"""

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
