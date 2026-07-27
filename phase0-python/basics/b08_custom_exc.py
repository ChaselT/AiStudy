class WithdrawError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def withdraw(balance, amount):
    if amount < 0:
        raise ValueError("Withdrawal amount cannot be negative")
    if amount > balance:
        raise WithdrawError("Insufficient funds for withdrawal")
    return balance - amount


def main():
    try:
        withdraw(100, 200)
    except WithdrawError as e:
        print(f"Caught an error: {e}")
    try:
        withdraw(100, -50)
    except ValueError as e:
        print(f"Caught an error: {e}")


if __name__ == "__main__":
    main()
