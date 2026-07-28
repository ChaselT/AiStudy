from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: str
    quantity: str


class Recipe(BaseModel):
    name: str
    ingredients: list[Ingredient] = Field(default_factory=list)


def main():
    a = Ingredient(name="Flour", quantity="2 cups")
    b = Ingredient(name="Sugar", quantity="1 cup")
    recipe = Recipe(name="Cake", ingredients=[a, b])
    print(recipe.model_dump_json())
    print(Recipe.model_json_schema())
    recipe2 = Recipe(name="No Ingredients")
    print(recipe2.model_dump_json())


if __name__ == "__main__":
    main()
