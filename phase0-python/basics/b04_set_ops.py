def main():

    english = {"user1", "user3"}
    math = {"user1", "user2"}
    print("英语和数学都选的学生：", english & math)
    print("只选英语的学生：", english - math)
    print("只选数学的学生：", math - english)
    print("选了至少一门课程的学生：", english | math)


if __name__ == "__main__":
    main()
