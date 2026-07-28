from pydantic import BaseModel, Field, ValidationError


class Movie(BaseModel):
    title: str = Field(..., description="The title of the movie")
    year: int = Field(ge=1900, le=2030, description="The release year of the movie")
    rating: float = Field(ge=0, le=10, description="The rating of the movie")


def main():
    try:
        a = Movie(title="Inception", year=2010, rating=8.8)
        print(a)
    except ValidationError as e:
        print(e)
    try:
        b = Movie(title="Invalid Movie", year=1800, rating=10)
        print(b)
    except ValidationError as e:
        print(e)
    try:
        c = Movie(title="Another Invalid Movie", year=2025, rating=15)
        print(c)
    except ValidationError as e:
        print(e)
    try:
        f = Movie(title="Yet Another Invalid Movie", year=2040, rating=-1)
        print(f)
    except ValidationError as e:
        print(e)

    d = Movie(title="Valid Movie", year=2022, rating=7.5)
    json_str = d.model_dump_json()
    print(json_str)
    restored = Movie.model_validate_json(json_str)
    print(restored)


if __name__ == "__main__":
    main()
