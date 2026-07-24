def main():
    line = " Tom, 25 , Beijing "

    s = line.split(",")  # 按逗号分割字符串
    s[0] = s[0].strip()  # 去掉第一个元素首尾的空格
    s[1] = s[1].strip()  # 去掉第二个元素首尾的空格
    s[2] = s[2].strip()  # 去掉第三个元素首尾的空格
    print(s)  # 输出分割后的列表
    result = "|".join(s)  # 将列表元素用|连接成字符串
    print(result)  # 输出连接后的字符串


if __name__ == "__main__":
    main()
