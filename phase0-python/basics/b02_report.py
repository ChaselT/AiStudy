def main():
    name1 = "显示器"
    price1 = 1000.12
    name2 = "键盘"
    price2 = 200.68
    name3 = "鼠标"
    price3 = 100.00
    print(f"{'商品名':<8}|{'价格元':>10}|")
    print(f"{name1:<8}|{price1:>10.2f}元|")
    print(f"{name2:<8}|{price2:>10.2f}元|")
    print(f"{name3:<8}|{price3:>10.2f}元|")

    


if __name__ == "__main__":
    main()
