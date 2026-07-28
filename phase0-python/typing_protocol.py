from typing import Protocol


class Notifier(Protocol):
    def send(self, msg: str) -> bool: ...


class ConsoleNotifier:
    def send(self, msg: str) -> bool:
        print(f"ConsoleNotifier: {msg}")
        return len(msg) > 0


class FileNotifier:
    def send(self, msg: str) -> bool:
        print(f"FileNotifier: {msg}")
        return len(msg) > 0


def broadcast(notifiers: list[Notifier], msg: str) -> None:
    for notifier in notifiers:
        notifier.send(msg)


# typing_protocol.py:21: error: Incompatible return value type (got "str", expected "bool")  [return-value]
# typing_protocol.py:35: error: Argument 1 to "boardcast" has incompatible type "ConsoleNotifier"; expected "Notifier"  [arg-type]
# typing_protocol.py:35: note: Following member(s) of "ConsoleNotifier" have conflicts:
# typing_protocol.py:35: note:     Expected:
# typing_protocol.py:35: note:         def send(self, msg: str) -> str
# typing_protocol.py:35: note:     Got:
# typing_protocol.py:35: note:         def send(self, msg: str) -> bool
# typing_protocol.py:36: error: Argument 1 to "boardcast" has incompatible type "FileNotifier"; expected "Notifier"  [arg-type]
# typing_protocol.py:36: note: Following member(s) of "FileNotifier" have conflicts:
# typing_protocol.py:36: note:     Expected:
# typing_protocol.py:36: note:         def send(self, msg: str) -> str
# typing_protocol.py:36: note:     Got:
# typing_protocol.py:36: note:         def send(self, msg: str) -> bool


def main() -> None:
    console_notifier = ConsoleNotifier()
    file_notifier = FileNotifier()

    broadcast([console_notifier, file_notifier], "Hello, World!")


if __name__ == "__main__":
    main()
