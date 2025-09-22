from typing import Any


def tprint(content: Any) -> None:
    """
    Print a content with a line of '=' before and after it.
    """
    print("\n" + "=" * 100)
    print(content)
    print("\n" + "=" * 100)
