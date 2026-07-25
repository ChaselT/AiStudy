def main():
    user = {
        "name": "张三",
        "age": 31,
        "gender": "男",
        "skill": ["Python", "Java", "C++"],
    }
    print(user["name"])
    print(user.get("email", "未知"))
    user["phone"] = "13800138000"
    for key, value in user.items():
        print(key, value)


if __name__ == "__main__":
    main()
