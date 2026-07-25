def main():

    courses = ["Python", "Java", "C++", "JavaScript", "Go", "Rust"]
    scores = [90, 70, 50, 80, 60, 40]
    for i, (course, score) in enumerate(zip(courses, scores)):
        print(f"{i + 1}. {course}: {score}")
        match score // 10:
            case 9 | 10:
                print(f"{course}: A")
            case 6 | 7 | 8:
                print(f"{course}: B")
            case _:
                print(f"{course}: C")


if __name__ == "__main__":
    main()
