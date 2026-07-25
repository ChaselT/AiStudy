def main():
    matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]

    print(matrix[0][0])  # 输出第一行第一列的元素
    print(matrix[1][1])  # 输出第二行第二列的元素
    print(matrix[2][2])  # 输出第三行第三列的元素
    print(sum(matrix[0]))     # 输出第一行的和
    print(sum(matrix[1]))     # 输出第二行的和
    print(sum(matrix[2]))     # 输出第三行的和


if __name__ == "__main__":
    main()
