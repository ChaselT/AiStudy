def main():
    s = [5,3,8,1]
    s.append(9)  # 在列表末尾添加元素9
    print(s)  # 输出列表
    s.insert(0, 0)  # 在索引0的位置插入元素0
    print(s)  # 输出列表
    s.remove(100)
    s.remove(3)  # 删除列表中第一个出现的元素3
    print(s)  # 输出列表
    s.sort()  # 对列表进行升序排序
    print(s)  # 输出列表
    print(max(s))  # 获取列表中的最大值
    print(min(s))  # 获取列表中的最小值
    print(sum(s))  # 获取列表中所有元素的和

if __name__ == "__main__":
    main()
