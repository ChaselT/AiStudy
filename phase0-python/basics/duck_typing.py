class JsonReport:
    def render(self) -> str:
        return '{"report": "A"}'


class TextReport:
    def render(self) -> str:
        return "report: B"


def print_report(report):
    print(report.render())


def main():

    print_report(JsonReport())
    print_report(TextReport())


if __name__ == "__main__":
    main()
