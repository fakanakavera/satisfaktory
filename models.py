from __future__ import annotations  # This allows us to use 'Recipe' in type hints before it's defined
from typing import List, Tuple, Dict

class Base:
    def __init__(self, base_id: int, name: str):
        """
        Initialize a Base object.

        Args:
            base_id (int): The unique identifier for the base.
            name (str): The name of the base.
        """
        self.base_id: int = base_id
        self.name: str = name
        self.nodes: Dict[int, ResourceNode] = {}
        self.facilities: Dict[int, Facility] = {}
        self.storage: Dict[str, float] = {}  # To keep track of item quantities in the base

    def add_node(self, node: 'ResourceNode') -> None:
        """
        Add a resource node to the base.

        Args:
            node (ResourceNode): The resource node to be added.
        """
        self.nodes[node.node_id] = node

    def add_facility(self, facility: 'Facility') -> None:
        """
        Add a facility to the base.

        Args:
            facility (Facility): The facility to be added.
        """
        self.facilities[facility.facility_id] = facility

    def update_storage(self, item: str, quantity: float) -> None:
        """
        Update the storage of an item in the base.

        Args:
            item (str): The name of the item.
            quantity (float): The quantity to be added (or subtracted if negative).
        """
        if item in self.storage:
            self.storage[item] += quantity
        else:
            self.storage[item] = quantity

class ResourceNode:
    def __init__(self, node_id: int, resource_type: str, purity: str, miner_type: str, miner_rate: float):
        """
        Initialize a ResourceNode object.

        Args:
            node_id (int): The unique identifier for the node.
            resource_type (str): The type of resource this node produces.
            purity (str): The purity level of the node ("Impure", "Normal", or "Pure").
            miner_type (str): The type of miner attached to this node.
            miner_rate (float): The base extraction rate of the miner in items per minute.
        """
        self.node_id: int = node_id
        self.resource_type: str = resource_type
        self.purity: str = purity
        self.miner_type: str = miner_type
        self.miner_rate: float = miner_rate
        self.clock_speed: float = 100.0  # Default clock speed is 100%
        self.output_rate: float = self.calculate_output_rate()

    def calculate_output_rate(self) -> float:
        """
        Calculate the output rate of the resource node based on purity, miner rate, and clock speed.

        Returns:
            float: The calculated output rate in items per minute.
        """
        purity_multiplier = {"Impure": 0.5, "Normal": 1, "Pure": 2}
        return purity_multiplier[self.purity] * self.miner_rate * (self.clock_speed / 100.0)

    def set_clock_speed(self, clock_speed: float) -> None:
        """
        Set the clock speed (overclock/underclock) for the resource node.

        Args:
            clock_speed (float): The new clock speed percentage (0.001% to 250%).
        """
        self.clock_speed = max(0.001, min(250, clock_speed))
        self.output_rate = self.calculate_output_rate()

class Facility:
    def __init__(self, facility_id: int, facility_type: str, recipe: str):
        """
        Initialize a Facility object.

        Args:
            facility_id (int): The unique identifier for the facility.
            facility_type (str): The type of the facility.
            recipe (str): The name of the recipe this facility is using.
        """
        self.facility_id: int = facility_id
        self.facility_type: str = facility_type
        self.recipe: str = recipe
        self.input_items: List[Tuple[str, float]] = []
        self.output_items: List[Tuple[str, float]] = []
        self.clock_speed: float = 100.0  # Default clock speed is 100%
        self.is_active: bool = True  # Always set is_active to True by default

    def set_input_item(self, item: str, rate: float) -> None:
        """
        Set an input item for the facility.

        Args:
            item (str): The name of the input item.
            rate (float): The consumption rate of the item.
        """
        self.input_items.append((item, rate))

    def set_output_item(self, item: str, rate: float) -> None:
        """
        Set an output item for the facility.

        Args:
            item (str): The name of the output item.
            rate (float): The production rate of the item.
        """
        self.output_items.append((item, rate))

    def get_production_rates(self) -> Dict[str, Dict[str, float]]:
        """
        Get the production rates for input and output items.

        Returns:
            Dict[str, Dict[str, float]]: A dictionary containing input and output rates.
        """
        return {
            "input": dict(self.input_items),
            "output": dict(self.output_items)
        }

    def set_clock_speed(self, clock_speed: float) -> None:
        """
        Set the clock speed (overclock/underclock) for the facility.

        Args:
            clock_speed (float): The new clock speed percentage (0.001% to 250%).
        """
        self.clock_speed = max(0.001, min(250, clock_speed))

    def toggle_active_state(self) -> None:
        """
        Toggle the active state of the facility (on/off).
        """
        self.is_active = not self.is_active

    def get_adjusted_rates(self) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """
        Get the input and output rates adjusted for the current clock speed and active state.

        Returns:
            Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]: Adjusted input and output rates.
        """
        if not self.is_active:
            return [], []
        
        adjustment_factor = self.clock_speed / 100.0
        adjusted_inputs = [(item, rate * adjustment_factor) for item, rate in self.input_items]
        adjusted_outputs = [(item, rate * adjustment_factor) for item, rate in self.output_items]
        return adjusted_inputs, adjusted_outputs

    def update_recipe(self, recipe: Recipe) -> None:
        """
        Update the facility's recipe and recalculate input and output items.

        Args:
            recipe (Recipe): The new recipe to be used by the facility.
        """
        self.recipe = recipe.name
        self.input_items = recipe.inputs
        self.output_items = recipe.outputs
        # Reset clock speed to 100% when changing recipes
        self.clock_speed = 100.0

class ResourceType:
    def __init__(self, name: str):
        """
        Initialize a ResourceType object.

        Args:
            name (str): The name of the resource type.
        """
        self.name: str = name

class MinerType:
    def __init__(self, name: str, base_rate: float):
        """
        Initialize a MinerType object.

        Args:
            name (str): The name of the miner type.
            base_rate (float): The base extraction rate of the miner.
        """
        self.name: str = name
        self.base_rate: float = base_rate

class BuildingType:
    def __init__(self, name: str):
        """
        Initialize a BuildingType object.

        Args:
            name (str): The name of the building type.
        """
        self.name: str = name

class Recipe:
    def __init__(self, name: str, building_type: str, inputs: List[Tuple[str, float]], outputs: List[Tuple[str, float]]):
        """
        Initialize a Recipe object.

        Args:
            name (str): The name of the recipe.
            building_type (str): The type of building that can use this recipe.
            inputs (List[Tuple[str, float]]): A list of input items and their quantities.
            outputs (List[Tuple[str, float]]): A list of output items and their quantities.
        """
        self.name: str = name
        self.building_type: str = building_type
        self.inputs: List[Tuple[str, float]] = inputs
        self.outputs: List[Tuple[str, float]] = outputs

class GameData:
    def __init__(self):
        """
        Initialize a GameData object to store game-related data.
        """
        self.resource_types: List[ResourceType] = []
        self.miner_types: List[MinerType] = []
        self.building_types: List[BuildingType] = []
        self.recipes: List[Recipe] = []
        self.next_base_id: int = 1
        self.next_node_id: int = 1
        self.next_facility_id: int = 1

    def add_resource_type(self, name: str) -> None:
        """
        Add a new resource type to the game data.

        Args:
            name (str): The name of the resource type.
        """
        self.resource_types.append(ResourceType(name))

    def add_miner_type(self, name: str, base_rate: float) -> None:
        """
        Add a new miner type to the game data.

        Args:
            name (str): The name of the miner type.
            base_rate (float): The base extraction rate of the miner.
        """
        self.miner_types.append(MinerType(name, base_rate))

    def add_building_type(self, name: str) -> None:
        """
        Add a new building type to the game data.

        Args:
            name (str): The name of the building type.
        """
        self.building_types.append(BuildingType(name))

    def add_recipe(self, name: str, building_type: str, inputs: List[Tuple[str, float]], outputs: List[Tuple[str, float]]) -> None:
        """
        Add a new recipe to the game data.

        Args:
            name (str): The name of the recipe.
            building_type (str): The type of building that can use this recipe.
            inputs (List[Tuple[str, float]]): A list of input items and their quantities.
            outputs (List[Tuple[str, float]]): A list of output items and their quantities.
        """
        self.recipes.append(Recipe(name, building_type, inputs, outputs))

    def get_recipe_by_name(self, name: str) -> Recipe:
        """
        Get a recipe by its name.

        Args:
            name (str): The name of the recipe to retrieve.

        Returns:
            Recipe: The recipe object if found, None otherwise.
        """
        for recipe in self.recipes:
            if recipe.name == name:
                return recipe
        return None

    def get_next_base_id(self) -> int:
        """
        Get the next available base ID and increment the counter.

        Returns:
            int: The next available base ID.
        """
        base_id = self.next_base_id
        self.next_base_id += 1
        return base_id

    def get_next_node_id(self) -> int:
        """
        Get the next available node ID and increment the counter.

        Returns:
            int: The next available node ID.
        """
        node_id = self.next_node_id
        self.next_node_id += 1
        return node_id

    def get_next_facility_id(self) -> int:
        """
        Get the next available facility ID and increment the counter.

        Returns:
            int: The next available facility ID.
        """
        facility_id = self.next_facility_id
        self.next_facility_id += 1
        return facility_id

    def delete_resource_type(self, name: str) -> None:
        """
        Delete a resource type from the game data.

        Args:
            name (str): The name of the resource type to delete.
        """
        self.resource_types = [rt for rt in self.resource_types if rt.name != name]

    def delete_miner_type(self, name: str) -> None:
        """
        Delete a miner type from the game data.

        Args:
            name (str): The name of the miner type to delete.
        """
        self.miner_types = [mt for mt in self.miner_types if mt.name != name]

    def delete_building_type(self, name: str) -> None:
        """
        Delete a building type from the game data.

        Args:
            name (str): The name of the building type to delete.
        """
        self.building_types = [bt for bt in self.building_types if bt.name != name]

    def delete_recipe(self, name: str) -> None:
        """
        Delete a recipe from the game data.

        Args:
            name (str): The name of the recipe to delete.
        """
        self.recipes = [recipe for recipe in self.recipes if recipe.name != name]

