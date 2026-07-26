def apply_all(func, values):
    return [func(x) for x in values]


def main():

    # Example usage
    numbers = [1, 2, 3, 4, 5]
    squared_numbers = apply_all(lambda x: x**2, numbers)
    print(squared_numbers)
    strings = ["hello", "world"]
    uppercased_strings = apply_all(str.upper, strings)
    print(uppercased_strings)
    a = apply_all(str.upper, [])
    print(a)


if __name__ == "__main__":
    main()
