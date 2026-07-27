import random
import json
import datetime
import math


def main():

    random_numbers = [random.randint(1, 100) for _ in range(5)]
    print(f"生成的随机整数列表是：{random_numbers}")
    print(f"生成的随机整数列表的 JSON 表示是：{json.dumps(random_numbers)}")
    print(f"当前日期和时间是：{datetime.date.today()}")
    print(f"列表最大数的平方根是：{math.sqrt(max(random_numbers))}")


if __name__ == "__main__":
    main()
