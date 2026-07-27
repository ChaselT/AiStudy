PI = 3.14159


def area(r):
    return PI * r * r


def perimeter(r):
    return 2 * PI * r


def main():
    print(f"Area of circle with radius 5: {area(5)}")
    print(f"Perimeter of circle with radius 6: {perimeter(6)}")


if __name__ == "__main__":
    main()
