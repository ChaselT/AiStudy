def read_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("输入无效，请输入一个整数。")


def main():

    num = read_int("请输入一个整数：")
    print(f"您输入的整数的平方是：{num**2}")


if __name__ == "__main__":
    main()
