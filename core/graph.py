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
    storm: bool = False
    locked_cost: int = 0

    def current_cost(self, storm_rate=1.6):
        if self.storm and not self.selected:
            return round(self.weight * storm_rate)
        return self.weight
