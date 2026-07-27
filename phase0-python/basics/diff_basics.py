def add_book(book: str, books_list: list[str] = []) -> list[str]:
    books_list.append(book)
    print(f"已添加图书：{book}")
    return books_list


def add_book_fixed(book: str, books_list: list[str] | None = None) -> list[str]:
    if books_list is None:
        books_list = []
    books_list.append(book)
    print(f"已添加图书：{book}")
    return books_list


def main():

    print(f"当前图书列表：{add_book('Python编程')}")
    print(f"当前图书列表：{add_book('人工智能')}")

    print(f"当前图书列表：{add_book_fixed('机器学习')}")
    print(f"当前图书列表：{add_book_fixed('深度学习')}")

    a = 5
    b = 5
    print(f"a==b: {a == b}")
    print(f"a is b: {a is b}")

    nums1 = [1, 2, 3]
    nums2 = [1, 2, 3]
    print(f"nums1==nums2: {nums1 == nums2}")
    print(f"nums1 is nums2: {nums1 is nums2}")


if __name__ == "__main__":
    main()
