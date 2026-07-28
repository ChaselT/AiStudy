from dataclasses import dataclass


@dataclass
class Point:
    x: float
    y: float


def distance(p1: Point, p2: Point) -> float:
    return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5


def main():
    p1 = Point(0, 0)
    p2 = Point(3, 4)
    print(p1 == p2)
    print(distance(p1, p2))
    p3 = Point(0, 0)
    print(p1 == p3)


if __name__ == "__main__":
    main()
