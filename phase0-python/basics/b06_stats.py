def stats(*nums):
    def avg(nums):
        return sum(nums) / len(nums) if nums else 0

    return min(nums), max(nums), avg(nums)


def main():

    minimum, maximum, average = stats(1, 2, 3, 4, 5)
    print(f"Minimum: {minimum}, Maximum: {maximum}, Average: {average}")

    list1 = [1, 2, 3, 4, 5]
    minimum, maximum, average = stats(*list1)
    print(f"Minimum: {minimum}, Maximum: {maximum}, Average: {average}")


if __name__ == "__main__":
    main()
