from common.exceptions import NotFoundException
from domain_classes.lookup import Lookup
from domain_classes.storage_recipe import StorageRecipe
from domain_classes.ui_recipe import Recipe
from enums import SIMOS
from storage.internal.lookup_tables import get_lookup

default_yaml_view = Recipe(
    **{
        "name": "Yaml",
        "type": SIMOS.UI_RECIPE.value,
        "plugin": "@development-framework/dm-core-plugins/yaml",
    }
)
default_form_edit = Recipe(
    **{
        "name": "Edit",
        "type": SIMOS.UI_RECIPE.value,
        "plugin": "@development-framework/dm-core-plugins/form",
    }
)
default_list_recipe = Recipe(
    **{
        "name": "List",
        "type": SIMOS.UI_RECIPE.value,
        "plugin": "@development-framework/dm-core-plugins/generic-list",
        "dimensions": "*",
    }
)


def storage_recipe_provider(type: str, context: str | None = None) -> list[StorageRecipe]:
    if not context:
        return []

    try:
        lookup: Lookup = get_lookup(context)
    except NotFoundException as error:
        if context == "DMSS":
            return []
        raise error
    # Get type specific recipes
    storage_recipes = lookup.storage_recipes.get(type, [])
    # If no recipe link exists for the type, use the contexts default
    if not storage_recipes:
        storage_recipes = lookup.storage_recipes.get("_default_", [])

    return storage_recipes
