from typing import List

from utils.data_structure.find import get

PRIMITIVES = ["string", "number", "integer", "boolean"]

INDEX_PRIMITIVE_CONTAINED = False
INDEX_ARRAY_CONTAINED = True
INDEX_TYPE_CONTAINED = False


class RecipeAttribute:
    def __init__(self, name: str, is_contained: bool = None):
        self.name = name
        self.is_contained = is_contained


class Recipe:
    def __init__(self, name: str, plugin_name: str, attributes: List = None):
        self.name = name
        self.plugin = plugin_name
        self.recipe_attributes = {}
        if attributes:
            self._convert_attributes(attributes)

    def _convert_attributes(self, attributes):
        for attribute in attributes:
            name = get(attribute, "name")
            self.recipe_attributes[name] = RecipeAttribute(name=name, is_contained=get(attribute, "contained"))

    def is_contained(self, attribute):
        if self.plugin == "INDEX":
            return self.is_contained_in_index(attribute)

    def is_contained_in_index(self, attribute):
        attribute_name = get(attribute, "name")
        attribute_type = get(attribute, "type")
        is_array = get(attribute, "dimensions", default="") == "*"

        if attribute_name in self.recipe_attributes:
            ui_attribute = self.recipe_attributes[attribute_name]
            if ui_attribute is not None and ui_attribute.is_contained is not None:
                return ui_attribute.is_contained

        if attribute_type in PRIMITIVES:
            return INDEX_PRIMITIVE_CONTAINED
        else:
            if attribute_name == "attributes":
                return False
            elif is_array:
                return INDEX_ARRAY_CONTAINED
            else:
                return INDEX_TYPE_CONTAINED


class DefaultRecipe(Recipe):
    def __init__(self, plugin_name: str):
        super().__init__("Default", plugin_name=plugin_name)