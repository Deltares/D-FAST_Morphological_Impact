from typing import Callable, Type, TypeVar

T = TypeVar('T')  # Define a type variable

class ConfigProcessor:
    def __init__(self):
        self.processors = {}

    def register_processor(self, element_type: Type[T], processor: Callable[[str], T],):
        self.processors[element_type] = processor

    def process_config_value(self, element_type: Type[T], config_value: str) -> T:
        processor = self.processors.get(element_type)
        if processor:
            return processor(config_value)
        else:
            raise ValueError(f"No config value processor registered for type {element_type}")