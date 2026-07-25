def main():

    a = [0, 1, "", "hi", [], [0], None, {}]
    for i in a:
        print(f"{i} is {'truthy' if i else 'falsy'}") 


if __name__ == "__main__":
    main()
