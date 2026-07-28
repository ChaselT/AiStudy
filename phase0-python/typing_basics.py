def parse_scores(raw: list[str]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for line in raw:
        name, score_str = line.split(":")
        scores[name.strip()] = float(score_str.strip())
    return scores


def main() -> None:
    raw_scores = ["Alice: 85.5", "Bob: 92.0", "Charlie: 78.5"]
    scores = parse_scores(raw_scores)
    print(scores)


if __name__ == "__main__":
    main()
