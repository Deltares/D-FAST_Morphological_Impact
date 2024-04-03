from collections import namedtuple

import pytest

# Define a named tuple to represent test cases
TestCase_display_needs_tide_old_zmin_zmax = namedtuple(
    "TestCase", ["display", "needs_tide", "old_zmin_zmax"]
)
TestCase_display_old_zmin_zmax = namedtuple("TestCase", ["display", "old_zmin_zmax"])
TestCase_needs_tide_old_zmin_zmax = namedtuple(
    "TestCase", ["needs_tide", "old_zmin_zmax"]
)


@pytest.fixture(
    params=[
        TestCase_display_needs_tide_old_zmin_zmax(
            display=False, needs_tide=False, old_zmin_zmax=False
        ),
        TestCase_display_needs_tide_old_zmin_zmax(
            display=True, needs_tide=False, old_zmin_zmax=False
        ),
        TestCase_display_needs_tide_old_zmin_zmax(
            display=True, needs_tide=True, old_zmin_zmax=False
        ),
        TestCase_display_needs_tide_old_zmin_zmax(
            display=True, needs_tide=True, old_zmin_zmax=True
        ),
        TestCase_display_needs_tide_old_zmin_zmax(
            display=False, needs_tide=True, old_zmin_zmax=False
        ),
        TestCase_display_needs_tide_old_zmin_zmax(
            display=False, needs_tide=True, old_zmin_zmax=True
        ),
        TestCase_display_needs_tide_old_zmin_zmax(
            display=False, needs_tide=False, old_zmin_zmax=True
        ),
        TestCase_display_needs_tide_old_zmin_zmax(
            display=True, needs_tide=False, old_zmin_zmax=True
        ),
    ],
    ids=lambda tc: f"display={tc.display}, needs_tide={tc.needs_tide}, old_zmin_zmax={tc.old_zmin_zmax}",
)
def display_needs_tide_old_zmin_zmax(request):
    return request.param


@pytest.fixture(
    params=[
        TestCase_display_old_zmin_zmax(display=False, old_zmin_zmax=False),
        TestCase_display_old_zmin_zmax(display=True, old_zmin_zmax=False),
        TestCase_display_old_zmin_zmax(display=True, old_zmin_zmax=True),
        TestCase_display_old_zmin_zmax(display=False, old_zmin_zmax=True),
    ],
    ids=lambda tc: f"display={tc.display}, old_zmin_zmax={tc.old_zmin_zmax}",
)
def display_old_zmin_zmax(request):
    return request.param


@pytest.fixture(
    params=[
        TestCase_needs_tide_old_zmin_zmax(needs_tide=False, old_zmin_zmax=False),
        TestCase_needs_tide_old_zmin_zmax(needs_tide=True, old_zmin_zmax=False),
        TestCase_needs_tide_old_zmin_zmax(needs_tide=True, old_zmin_zmax=True),
        TestCase_needs_tide_old_zmin_zmax(needs_tide=False, old_zmin_zmax=True),
    ],
    ids=lambda tc: f"needs_tide={tc.needs_tide}, old_zmin_zmax={tc.old_zmin_zmax}",
)
def needs_tide_old_zmin_zmax(request):
    return request.param
