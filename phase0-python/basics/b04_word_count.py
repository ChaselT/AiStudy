def main():
    words = ["apple", "banana", "apple", "cherry", "banana", "apple"]
    word_count = {}
    for word in words:
        word_count[word] = word_count.get(word, 0) + 1
    for word, count in word_count.items():
        print(f"{word}: {count}")

if __name__ == "__main__":
    main()
