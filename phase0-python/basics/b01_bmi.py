

def main():
    weight = float(input("请输入体重(kg)："))
    height = float(input("请输入身高(m)："))
    bmi = weight / (height ** 2)
    print(f"体重：{weight}kg，身高：{height}m，BMI：{bmi:.2f}")


if __name__ == "__main__":
    main()