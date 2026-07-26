def describe(name, age=18, city="Unknown"):
    return f"{name} is {age} years old and lives in {city}."


def main():

    print(describe("Alice", 25, "New York"))
    print(describe(name="Bob", age=30, city="Los Angeles"))
    print(describe("Charlie", city="Chicago", age=18))


if __name__ == "__main__":
    main()
