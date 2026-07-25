def main():
    a,b,c = 1,2,3
    a,b,c = c,a,b
    print(a,b,c)  # 输出交换后的结果
    first, *rest = [10, 20, 30, 40]
    print(first,rest)  

if __name__ == "__main__":
    main()
