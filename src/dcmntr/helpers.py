from dataclasses import dataclass, field
from typing import Sequence, Callable, Any


def int_to_az(n: int) -> str:
    if n < 1:
        raise ValueError("Number must be >= 1")

    result = ""
    while n > 0:
        n -= 1
        result = chr(ord("a") + (n % 26)) + result
        n //= 26

    return result


def to_roman(n: int) -> str:
    if not 1 <= n <= 3999:
        raise ValueError("Roman numerals support 1..3999")

    symbols = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]

    result = []
    for value, symbol in symbols:
        count, n = divmod(n, value)
        result.append(symbol * count)
    return "".join(result)


class SectionNumbering:

    N = str
    az = int_to_az
    AZ = lambda n: int_to_az(n).upper()
    IV = to_roman
    iv = lambda n: to_roman(n).lower()

    def __init__(self, display: Sequence[Callable[[int], str]] = (IV, az, N)) -> None:
        self.display = tuple(display)
        self.counters = [0] * len(self.display)

    def next_numbers(self, level: int) -> tuple[int, ...]:
        """
        level: 2-based level. That means first level header is only one and not counted.
        """
        if not 2 <= level <= len(self.display) + 1:
            raise ValueError("Invalid header level")

        idx = level - 2
        self.counters[idx] += 1

        for i in range(idx + 1, len(self.display)):
            self.counters[i] = 0

        return tuple(self.counters[: level - 1])

    def next(self, level: int) -> str:
        return ".".join(f(n) for f, n in zip(self.display, self.next_numbers(level)))


@dataclass
class Anchors:
    anchors: dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, value: Any) -> Any:
        assert name not in self.anchors
        self.anchors[name] = value
        return value

    def get(self, name: str) -> Any:
        return self.anchors[name]

    def __len__(self) -> int:
        return len(self.anchors)
