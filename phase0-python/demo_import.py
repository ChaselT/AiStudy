print("我是裸露的语句，一被加载就执行")

def greet():
    print("greet 被调用了")

if __name__ == "__main__":
    print("我是直接运行才会执行的部分")
    greet()