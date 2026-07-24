def main():
    s = "hello python"

    print(s[0])  # 输出第一个字符
    print(s[-1])  # 输出最后一个字符
    print(s[0:5])  # 输出前五个字符
    print(s[:5])  # 输出前五个字符
    print(s[::-1])  # 输出整个字符串的逆序
    print(s[::2])  # 输出整个字符串的偶数索引字符


if __name__ == "__main__":
    main()
