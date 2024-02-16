from typing import Callable, Optional, Tuple, Type, TypeVar
from dfastmi.io.Reach import Reach
T = TypeVar('T')  # Define a type variable


class RiverConfigElementProcessor:
    def __init__(self):
        self.processors = {}
        self.parsers = {}

    def register_processor(self, element_type: Type[T], processor: Callable[[str, str, Reach], T], parser: Callable[[str], Tuple[T, ...]]):
        self.processors[element_type] = processor
        self.parsers[element_type] = parser

    def process_river_element(self, element_type: Type[T], key: str, entry_value: str, reach: Reach, default: Optional[T] = None, expected_number_of_values: Optional[int] = None) -> T:
        processor = self.processors.get(element_type)
        if processor:
            parser = self.parsers.get(element_type)
            if parser:
                return processor(key, entry_value, reach, parser, default, expected_number_of_values)
            else:
                raise ValueError(f"No string parser registered for type {element_type}")
        else:
            raise ValueError(f"No processor registered for type {element_type}")