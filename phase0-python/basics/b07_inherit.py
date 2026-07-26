class Shape:
    def __init__(self):
        self.name = "Shape"
        self.color = "Red"

    def area(self):
        return 0


class Rect(Shape):
    def __init__(self):
        super().__init__()
        self.name = "Rectangle"

    def area(self):
        return 1


class Circle(Shape):
    def __init__(self):
        super().__init__()
        self.name = "Circle"

    def area(self):
        return 3.14


def main():

    shapes = [Shape(), Rect(), Circle()]
    for shape in shapes:
        print(f"{shape.name} area: {shape.area()} color: {shape.color}")


if __name__ == "__main__":
    main()
