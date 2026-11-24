from dataclasses import dataclass


@dataclass
class Island:
    id: int
    x: float
    y: float


@dataclass(eq=False)
class Bridge:
    a: int
    b: int
    weight: int
    selected: bool = False
