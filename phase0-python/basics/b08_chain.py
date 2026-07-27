def parse_price(s):
    try:
        return float(s.replace("$", "").replace(",", ""))
    except ValueError as e:
        raise ValueError(f"Invalid price format: {s}") from e


def main():

    prices = ["$1,234.56", "$789.00", "invalid"]
    for price in prices:
        parsed_price = parse_price(price)
        print(f"Parsed price: {parsed_price}")


if __name__ == "__main__":
    main()
