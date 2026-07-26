class BankAccount:
    def __init__(self, balance):
        self._balance = balance
        self._is_empty = balance <= 0

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if value < 0:
            raise ValueError("Balance cannot be negative")
        self._balance = value
        # self._is_empty = value <= 0

    @property
    def is_empty(self):
        return self._balance <= 0


def main():

    a = BankAccount(200)
    print(a.balance)
    try:
        a.balance = -100  # 尝试设置负余额
    except ValueError as e:
        print(f"拦截成功: {e}")
    print(a.balance)
    try:
        a.is_empty = True
    except AttributeError as e:
        print(f"拦截成功: {e}")
    print(a.is_empty)
    a.balance = 0
    print(a.is_empty)


if __name__ == "__main__":
    main()
