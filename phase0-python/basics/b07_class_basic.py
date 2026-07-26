class Book:
    def __init__(self, title, author, price):
        self.title = title
        self.author = author
        self.price = price

    def __repr__(self):
        return f"'{self.title}' by {self.author}, priced at ${self.price:.2f}"

    def discount(self, rate):
        self.price *= rate
        return self.price


def main():

    book1 = Book("1984", "George Orwell", 15.99)
    book2 = Book("To Kill a Mockingbird", "Harper Lee", 12.49)

    list_of_books = [book1, book2]

    print(list_of_books)
    print(Book.discount(book1, 0.9))
    print(book2.discount(0.8))


if __name__ == "__main__":
    main()
