import random
import string
from typing import List, Any, Iterator, TypeVar
from django.utils import timezone

T = TypeVar("T")


def generate_verification_code(length=6):
    return "".join(random.choices(string.digits, k=length))


class BatchProcessor:
    """Simple batch processor for processing items in chunks."""

    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size

    def process_in_batches(
        self, items: List[T], processor_func=None, batch_size: int = None
    ) -> Iterator[List[T]]:
        """
        Process items in batches.

        Args:
            items: List of items to process
            processor_func: Optional function to process each batch
            batch_size: Override default batch size

        Yields:
            Batches of items
        """
        batch_size = batch_size or self.batch_size
        total_items = len(items)

        for i in range(0, total_items, batch_size):
            batch = items[i : i + batch_size]

            if processor_func:
                processor_func(batch)

            yield batch

    def get_metrics(self) -> dict:
        """Get processing metrics."""
        return {"batch_size": self.batch_size, "timestamp": timezone.now().isoformat()}


batch_processor = BatchProcessor()
