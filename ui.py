from typing import List, Dict, Optional, Tuple
from models import Facility, GameData, Base, ResourceNode, Recipe
from blessed import Terminal
from math import floor
from decimal import Decimal, ROUND_HALF_UP
from tabulate import tabulate

class UserInterface:
    def __init__(self, term: Terminal, game_data: GameData):
        """
        Initialize the UserInterface with a Terminal and GameData.

        Args:
            term (Terminal): The blessed Terminal object for UI rendering.
            game_data (GameData): The GameData object containing game information.
        """
        self.term = term
        self.game_data = game_data

    def display_main_menu(self) -> str:
        """
        Display the main menu and return the user's choice.

        Returns:
            str: The selected menu option.
        """
        options = [
            "Manage Game Data",
            "Manage Bases",
            "Manage Nodes",
            "Track Facilities",
            "View Production Rates",
            "View Net Production",
            "Identify Bottlenecks",
            "Exit"
        ]
        return self.display_menu("Satisfactory Production Tracker", options)

    def display_menu(self, title: str, options: List[str], allow_escape: bool = True) -> str:
        """
        Display a menu with the given title and options.

        Args:
            title (str): The title of the menu.
            options (List[str]): A list of menu options.
            allow_escape (bool, optional): Whether to allow ESC key to exit. Defaults to True.

        Returns:
            str: The selected menu option or "ESC" if escape is allowed and selected.
        """
        with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
            current_option = 0
            while True:
                print(self.term.home + self.term.clear)
                print(self.term.bold(title))
                print()

                for idx, option in enumerate(options):
                    if idx == current_option:
                        print(self.term.bold_green(f"> {option}"))
                    else:
                        print(f"  {option}")

                if allow_escape:
                    print("\nPress ESC to go back")

                key = self.term.inkey()
                if key.name == "KEY_UP" and current_option > 0:
                    current_option -= 1
                elif key.name == "KEY_DOWN" and current_option < len(options) - 1:
                    current_option += 1
                elif key.name == "KEY_ENTER":
                    return options[current_option]
                elif key.name == "KEY_ESCAPE" and allow_escape:
                    return "ESC"

    def get_base_input(self) -> Tuple[int, str]:
        """
        Get user input for creating a new base.

        Returns:
            Tuple[int, str]: A tuple containing the base ID and name.
        """
        base_id = self.game_data.get_next_base_id()
        name = input("Enter base name: ")
        return base_id, name

    def get_node_input(self) -> Tuple[int, str, str, str, float]:
        """
        Get user input for creating a new resource node.

        Returns:
            Tuple[int, str, str, str, float]: A tuple containing the node ID, resource type, purity, miner type, and miner rate.
        """
        node_id = self.game_data.get_next_node_id()
        resource_type = self.select_from_list("Select resource type", [rt.name for rt in self.game_data.resource_types])
        purity = self.select_from_list("Select purity", ["Impure", "Normal", "Pure"])
        miner_type = self.select_from_list("Select miner type", [mt.name for mt in self.game_data.miner_types])
        
        # Get the base rate for the selected miner type
        base_rate = next(mt.base_rate for mt in self.game_data.miner_types if mt.name == miner_type)
        
        # Allow the user to adjust the miner rate
        while True:
            try:
                miner_rate = float(input(f"Enter miner rate (default is {base_rate}): ") or base_rate)
                if miner_rate > 0:
                    break
                else:
                    print("Miner rate must be greater than 0.")
            except ValueError:
                print("Please enter a valid number.")
        
        return node_id, resource_type, purity, miner_type, miner_rate

    def get_facility_input(self) -> Facility:
        """
        Get user input for creating a new facility.

        Returns:
            Facility: A new Facility object based on user input.
        """
        facility_id = self.game_data.get_next_facility_id()
        facility_type = self.select_from_list("Select facility type", [bt.name for bt in self.game_data.building_types])
        
        # Filter recipes for the selected facility type
        valid_recipes = [recipe for recipe in self.game_data.recipes if recipe.building_type == facility_type]
        recipe_names = [recipe.name for recipe in valid_recipes] + ["Custom"]
        
        recipe = self.select_from_list("Select recipe", recipe_names)
        
        if recipe == "Custom":
            return self.get_custom_facility_input(facility_id, facility_type)
        
        selected_recipe = self.game_data.get_recipe_by_name(recipe)
        facility = Facility(facility_id, facility_type, recipe)
        
        for item, rate in selected_recipe.inputs:
            facility.set_input_item(item, rate)
        
        for item, rate in selected_recipe.outputs:
            facility.set_output_item(item, rate)
        
        return facility

    def get_custom_facility_input(self, facility_id: int, facility_type: str) -> Facility:
        """
        Get user input for creating a custom facility.

        Args:
            facility_id (int): The ID of the facility.
            facility_type (str): The type of the facility.

        Returns:
            Facility: A new custom Facility object based on user input.
        """
        recipe = "Custom"
        facility = Facility(facility_id, facility_type, recipe)
        
        print("Enter input items (press Enter with empty item name to finish):")
        while True:
            item = input("Input item name: ")
            if not item:
                break
            rate = float(input(f"Input rate for {item} (items per minute): "))
            facility.set_input_item(item, rate)
        
        print("Enter output items (press Enter with empty item name to finish):")
        while True:
            item = input("Output item name: ")
            if not item:
                break
            rate = float(input(f"Output rate for {item} (items per minute): "))
            facility.set_output_item(item, rate)
        
        return facility

    def display_production_rates(self, production: Dict[str, float], consumption: Dict[str, float], limiting_factors: Dict[str, List[str]]) -> None:
        """
        Display the production rates, consumption rates, and limiting factors for all resources.

        Args:
            production (Dict[str, float]): A dictionary of resource production rates.
            consumption (Dict[str, float]): A dictionary of resource consumption rates.
            limiting_factors (Dict[str, List[str]]): A dictionary of limiting factors for each resource.
        """
        print(self.term.bold_green + self.term.center("=== Production and Consumption Rates ==="))
        print(self.term.normal)  # Reset text formatting

        all_items = sorted(set(production.keys()) | set(consumption.keys()))

        # Display detailed production and consumption rates
        for item in all_items:
            prod_rate = production.get(item, 0)
            cons_rate = consumption.get(item, 0)

            print(f"{item}:")
            print(f"  Production: {prod_rate:.2f}/min")
            print(f"  Consumption: {cons_rate:.2f}/min")

            if item in limiting_factors:
                print(f"  Limited by: {', '.join(limiting_factors[item])}")

            print()  # Add a blank line between items

    def display_net_production(self, bases: Dict[int, Base], production_graph) -> None:
        """
        Display the net production rates for resources in a selected base.

        Args:
            bases (Dict[int, Base]): A dictionary of all bases.
            production_graph: The ProductionGraph object to calculate production rates.
        """
        if not bases:
            print(self.term.clear + "No bases available.")
            input("Press Enter to continue...")
            return

        base_id = self.select_base(bases)
        if base_id is None:
            return

        base = bases[base_id]
        production, consumption = production_graph.calculate_production_rates_for_base(base_id)

        print(self.term.clear)
        print(self.term.bold_green + self.term.center(f"=== Net Production Rates for Base: {base.name} ==="))
        print(self.term.normal)  # Reset text formatting

        all_items = sorted(set(production.keys()) | set(consumption.keys()))
        net_production = {}

        for item in all_items:
            prod_rate = production.get(item, 0)
            cons_rate = consumption.get(item, 0)
            net_rate = self.round_float(prod_rate - cons_rate, 2)
            
            net_production[item] = net_rate
            print(f"{item:20}: {net_rate:8.2f}/min (Production: {self.round_float(prod_rate, 2):8.2f}/min, Consumption: {self.round_float(cons_rate, 2):8.2f}/min)")

        print("\n" + self.term.bold_green + "Possible Recipes:" + self.term.normal)
        possible_recipes = self.calculate_possible_recipes(net_production)
        if possible_recipes:
            for recipe_name, max_crafts in possible_recipes.items():
                print(f"{recipe_name:30}: {max_crafts} times")
        else:
            print("No recipes can be crafted with the current net production.")

        input("Press Enter to continue...")

    @staticmethod
    def round_float(value: float, decimal_places: int) -> float:
        """
        Round a float value to the specified number of decimal places.

        Args:
            value (float): The value to round.
            decimal_places (int): The number of decimal places to round to.

        Returns:
            float: The rounded value.
        """
        return float(Decimal(str(value)).quantize(Decimal(f'0.{"0" * decimal_places}'), rounding=ROUND_HALF_UP))

    def display_bottlenecks(self, bottlenecks: Dict[str, float]) -> None:
        """
        Display the bottlenecks in resource production.

        Args:
            bottlenecks (Dict[str, float]): A dictionary of resource bottlenecks and their deficit amounts.
        """
        print("Bottlenecks:")
        for item, deficit in bottlenecks.items():
            print(f"{item}: {deficit} per minute shortage")

    def display_facility_details(self, facility: Facility) -> None:
        """
        Display detailed information about a facility.

        Args:
            facility (Facility): The Facility object to display details for.
        """
        print(f"\nFacility: {facility.facility_id}")
        print(f"Type: {facility.facility_type}")
        print(f"Recipe: {facility.recipe}")
        print(f"Clock Speed: {facility.clock_speed}%")
        adjusted_inputs, adjusted_outputs = facility.get_adjusted_rates()
        print("Inputs:")
        for item, rate in adjusted_inputs:
            print(f"  {item}: {rate:.2f} per minute")
        print("Outputs:")
        for item, rate in adjusted_outputs:
            print(f"  {item}: {rate:.2f} per minute")

    def display_base_management_menu(self) -> str:
        """
        Display the base management menu and return the user's choice.

        Returns:
            str: The selected menu option.
        """
        options = ["Add New Base", "View All Bases", "Delete Base", "Return to Main Menu"]
        return self.display_menu("Base Management", options)

    def display_game_data_menu(self) -> str:
        """
        Display the game data management menu and return the user's choice.

        Returns:
            str: The selected menu option.
        """
        options = ["Manage Resource Types", "Manage Miner Types", "Manage Building Types", "Manage Recipes", "Return to Main Menu"]
        return self.display_menu("Game Data Management", options)

    def manage_resource_types(self) -> None:
        """
        Handle the resource type management menu and user interactions.
        """
        while True:
            options = [rt.name for rt in self.game_data.resource_types] + ["Add New Resource Type", "Delete Resource Type", "Return to Game Data Menu"]
            choice = self.display_menu("Manage Resource Types", options)
            if choice == "ESC" or choice == "Return to Game Data Menu":
                break
            elif choice == "Add New Resource Type":
                name = input("Enter new resource type name: ")
                self.game_data.add_resource_type(name)
            elif choice == "Delete Resource Type":
                self.delete_resource_type()

    def manage_miner_types(self) -> None:
        """
        Handle the miner type management menu and user interactions.
        """
        while True:
            options = [f"{mt.name} (Base rate: {mt.base_rate})" for mt in self.game_data.miner_types] + ["Add New Miner Type", "Delete Miner Type", "Return to Game Data Menu"]
            choice = self.display_menu("Manage Miner Types", options)
            if choice == "Add New Miner Type":
                name = input("Enter new miner type name: ")
                base_rate = float(input("Enter base rate for the miner: "))
                self.game_data.add_miner_type(name, base_rate)
            elif choice == "Delete Miner Type":
                self.delete_miner_type()
            elif choice == "Return to Game Data Menu":
                break

    def manage_building_types(self) -> None:
        """
        Handle the building type management menu and user interactions.
        """
        while True:
            options = [bt.name for bt in self.game_data.building_types] + ["Add New Building Type", "Delete Building Type", "Return to Game Data Menu"]
            choice = self.display_menu("Manage Building Types", options)
            if choice == "Add New Building Type":
                name = input("Enter new building type name: ")
                self.game_data.add_building_type(name)
            elif choice == "Delete Building Type":
                self.delete_building_type()
            elif choice == "Return to Game Data Menu":
                break

    def select_from_list(self, prompt: str, options: List[str]) -> str:
        """
        Display a list of options and let the user select one.

        Args:
            prompt (str): The prompt to display above the list.
            options (List[str]): A list of options to choose from.

        Returns:
            str: The selected option.
        """
        return self.display_menu(prompt, options)

    def display_node_management_menu(self) -> str:
        """
        Display the node management menu and return the user's choice.

        Returns:
            str: The selected menu option.
        """
        options = ["Add New Node", "Link Existing Node to Base", "Overclock Node", "Delete Node", "Return to Main Menu"]
        return self.display_menu("Node Management", options)

    def select_base(self, bases: Dict[int, Base]) -> Optional[int]:
        """
        Let the user select a base from the list of available bases.

        Args:
            bases (Dict[int, Base]): A dictionary of available bases.

        Returns:
            Optional[int]: The ID of the selected base, or None if no base was selected.
        """
        if not bases:
            print("No bases available. Please create a base first.")
            return None

        options = [f"{base.base_id}: {base.name}" for base in bases.values()]
        options.append("Cancel")
        choice = self.select_from_list("Select a base", options)
        
        if choice == "Cancel":
            return None
        return int(choice.split(":")[0])

    def select_node(self, nodes: Dict[int, ResourceNode]) -> Optional[ResourceNode]:
        """
        Let the user select a node from the list of available nodes.

        Args:
            nodes (Dict[int, ResourceNode]): A dictionary of available nodes.

        Returns:
            Optional[ResourceNode]: The selected ResourceNode, or None if no node was selected.
        """
        if not nodes:
            print("No nodes available.")
            return None

        options = [f"{node.node_id}: {node.resource_type} ({node.purity})" for node in nodes.values()]
        options.append("Cancel")
        choice = self.select_from_list("Select a node", options)
        
        if choice == "Cancel":
            return None
        node_id = int(choice.split(":")[0])
        return nodes[node_id]

    def manage_recipes(self) -> None:
        """
        Handle the recipe management menu and user interactions.
        """
        while True:
            options = [recipe.name for recipe in self.game_data.recipes] + ["Add New Recipe", "Delete Recipe", "Return to Game Data Menu"]
            choice = self.display_menu("Manage Recipes", options)
            if choice == "ESC" or choice == "Return to Game Data Menu":
                break
            elif choice == "Add New Recipe":
                self.add_new_recipe()
            elif choice == "Delete Recipe":
                self.delete_recipe()
            else:
                self.view_recipe_details(choice)

    def add_new_recipe(self) -> None:
        """
        Handle the process of adding a new recipe based on user input.
        """
        if not self.game_data.resource_types:
            print("No resource types registered. Please add some resource types first.")
            return
        if not self.game_data.building_types:
            print("No building types registered. Please add some building types first.")
            return

        name = input("Enter recipe name: ")
        building_type = self.select_from_list("Select building type", [bt.name for bt in self.game_data.building_types])
        inputs = []
        outputs = []

        print("Enter input items (select 'Done' to finish):")
        while True:
            item = self.select_from_list("Select input item", [rt.name for rt in self.game_data.resource_types] + ["Done"])
            if item == "Done":
                break
            quantity = float(input(f"Quantity of {item}: "))
            inputs.append((item, quantity))

        print("Enter output items (select 'Done' to finish):")
        while True:
            item = self.select_from_list("Select output item", [rt.name for rt in self.game_data.resource_types] + ["Done"])
            if item == "Done":
                break
            quantity = float(input(f"Quantity of {item}: "))
            outputs.append((item, quantity))

        self.game_data.add_recipe(name, building_type, inputs, outputs)
        print(f"Recipe '{name}' added successfully.")

    def view_recipe_details(self, recipe_name: str) -> None:
        """
        Display detailed information about a specific recipe.

        Args:
            recipe_name (str): The name of the recipe to display details for.
        """
        recipe = self.game_data.get_recipe_by_name(recipe_name)
        if recipe:
            print(f"\nRecipe: {recipe.name}")
            print(f"Building Type: {recipe.building_type}")
            print("Inputs:")
            for item, quantity in recipe.inputs:
                print(f"  {item}: {quantity}")
            print("Outputs:")
            for item, quantity in recipe.outputs:
                print(f"  {item}: {quantity}")
        else:
            print(f"Recipe '{recipe_name}' not found.")
        input("Press Enter to continue...")

    def delete_resource_type(self) -> None:
        """
        Handle the process of deleting a resource type based on user input.
        """
        options = [rt.name for rt in self.game_data.resource_types] + ["Cancel"]
        choice = self.select_from_list("Select resource type to delete", options)
        if choice != "Cancel":
            self.game_data.delete_resource_type(choice)
            print(f"Resource type '{choice}' deleted successfully.")

    def delete_miner_type(self) -> None:
        """
        Handle the process of deleting a miner type based on user input.
        """
        options = [f"{mt.name} (Base rate: {mt.base_rate})" for mt in self.game_data.miner_types] + ["Cancel"]
        choice = self.select_from_list("Select miner type to delete", options)
        if choice != "Cancel":
            miner_name = choice.split(" (")[0]
            self.game_data.delete_miner_type(miner_name)
            print(f"Miner type '{miner_name}' deleted successfully.")

    def delete_building_type(self) -> None:
        """
        Handle the process of deleting a building type based on user input.
        """
        options = [bt.name for bt in self.game_data.building_types] + ["Cancel"]
        choice = self.select_from_list("Select building type to delete", options)
        if choice != "Cancel":
            self.game_data.delete_building_type(choice)
            print(f"Building type '{choice}' deleted successfully.")

    def delete_recipe(self) -> None:
        """
        Handle the process of deleting a recipe based on user input.
        """
        options = [recipe.name for recipe in self.game_data.recipes] + ["Cancel"]
        choice = self.select_from_list("Select recipe to delete", options)
        if choice != "Cancel":
            self.game_data.delete_recipe(choice)
            print(f"Recipe '{choice}' deleted successfully.")

    def delete_base(self, bases: Dict[int, Base]) -> Optional[int]:
        """
        Let the user select a base to delete from the list of available bases.

        Args:
            bases (Dict[int, Base]): A dictionary of available bases.

        Returns:
            Optional[int]: The ID of the base to delete, or None if no base was selected.
        """
        if not bases:
            print("No bases available to delete.")
            return None

        options = [f"{base.base_id}: {base.name}" for base in bases.values()] + ["Cancel"]
        choice = self.select_from_list("Select base to delete", options)
        if choice != "Cancel":
            base_id = int(choice.split(":")[0])
            return base_id
        return None

    def delete_node(self, nodes: Dict[int, ResourceNode]) -> Optional[int]:
        """
        Let the user select a node to delete from the list of available nodes.

        Args:
            nodes (Dict[int, ResourceNode]): A dictionary of available nodes.

        Returns:
            Optional[int]: The ID of the node to delete, or None if no node was selected.
        """
        if not nodes:
            print("No nodes available to delete.")
            return None

        options = [f"{node.node_id}: {node.resource_type} ({node.purity})" for node in nodes.values()] + ["Cancel"]
        choice = self.select_from_list("Select node to delete", options)
        if choice != "Cancel":
            node_id = int(choice.split(":")[0])
            return node_id
        return None

    def delete_facility(self, facilities: Dict[int, Facility]) -> Optional[int]:
        """
        Let the user select a facility to delete from the list of available facilities.

        Args:
            facilities (Dict[int, Facility]): A dictionary of available facilities.

        Returns:
            Optional[int]: The ID of the facility to delete, or None if no facility was selected.
        """
        if not facilities:
            print("No facilities available to delete.")
            return None

        headers = ["ID", "Type", "Recipe", "Clock Speed"]
        table_data = [
            [facility.facility_id, facility.facility_type, facility.recipe, f"{facility.clock_speed:.1f}%"]
            for facility in facilities.values()
        ]
        
        # Sort the table data by the "Type" column (index 1)
        table_data.sort(key=lambda x: x[1])
        
        print(tabulate(table_data, headers=headers, tablefmt="plain"))
        
        while True:
            choice = input("Enter the ID of the facility to delete (or 'cancel' to go back): ")
            if choice.lower() == 'cancel':
                return None
            try:
                facility_id = int(choice)
                if facility_id in facilities:
                    return facility_id
                else:
                    print("Invalid facility ID. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or 'cancel'.")

    def calculate_possible_recipes(self, net_production: Dict[str, float]) -> Dict[str, int]:
        """
        Calculate the number of times each recipe can be crafted based on net production.

        Args:
            net_production (Dict[str, float]): A dictionary of net production rates for each resource.

        Returns:
            Dict[str, int]: A dictionary of recipe names and the number of times they can be crafted.
        """
        possible_recipes = {}
        for recipe in self.game_data.recipes:
            max_crafts = float('inf')
            for input_item, input_quantity in recipe.inputs:
                if input_item in net_production:
                    available_quantity = net_production[input_item]
                    if available_quantity > 0:
                        crafts = floor(available_quantity / input_quantity)
                        max_crafts = min(max_crafts, crafts)
                    else:
                        max_crafts = 0
                        break
                else:
                    max_crafts = 0
                    break
            if max_crafts > 0:
                possible_recipes[recipe.name] = max_crafts
        return possible_recipes

    def select_facility(self, facilities: Dict[int, Facility]) -> Optional[int]:
        """
        Let the user select a facility from the list of available facilities.

        Args:
            facilities (Dict[int, Facility]): A dictionary of available facilities.

        Returns:
            Optional[int]: The ID of the selected facility, or None if no facility was selected.
        """
        if not facilities:
            print("No facilities available.")
            return None

        headers = ["ID", "Type", "Recipe", "Clock Speed"]
        table_data = [
            [facility.facility_id, facility.facility_type, facility.recipe, f"{facility.clock_speed:.1f}%"]
            for facility in facilities.values()
        ]
        
        # Sort the table data by the "Type" column (index 1)
        table_data.sort(key=lambda x: x[1])
        
        print(tabulate(table_data, headers=headers, tablefmt="plain"))
        
        while True:
            choice = input("Enter the ID of the facility to select (or 'cancel' to go back): ")
            if choice.lower() == 'cancel':
                return None
            try:
                facility_id = int(choice)
                if facility_id in facilities:
                    return facility_id
                else:
                    print("Invalid facility ID. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or 'cancel'.")

    def select_recipe(self, recipes: List[Recipe], facility_type: Optional[str] = None) -> Optional[Recipe]:
        """
        Let the user select a recipe, optionally filtered by facility type.

        Args:
            recipes (List[Recipe]): A list of available recipes.
            facility_type (Optional[str]): The type of the facility to filter recipes, or None for all recipes.

        Returns:
            Optional[Recipe]: The selected Recipe object, or None if no recipe was selected.
        """
        valid_recipes = recipes if facility_type is None else [recipe for recipe in recipes if recipe.building_type == facility_type]
        if not valid_recipes:
            print(f"No recipes available{' for ' + facility_type if facility_type else ''}.")
            return None

        options = [f"{recipe.name} ({recipe.building_type})" for recipe in valid_recipes]
        options.append("Cancel")
        choice = self.select_from_list(f"Select a recipe{' for ' + facility_type if facility_type else ''}", options)
        
        if choice == "Cancel":
            return None
        selected_recipe_name = choice.split(" (")[0]
        return next(recipe for recipe in valid_recipes if recipe.name == selected_recipe_name)

    def get_clock_speed_input(self) -> float:
        """
        Get user input for the facility clock speed.

        Returns:
            float: The new clock speed percentage (0.001% to 250%).
        """
        while True:
            try:
                clock_speed = float(input("Enter new clock speed (0.001% to 250%): "))
                if 0.001 <= clock_speed <= 250:
                    return clock_speed
                else:
                    print("Clock speed must be between 0.001% and 250%.")
            except ValueError:
                print("Please enter a valid number.")

    def get_facility_count(self) -> int:
        """
        Get user input for the number of facilities to add.

        Returns:
            int: The number of facilities to add.
        """
        while True:
            try:
                count = int(input("Enter the number of facilities to add: "))
                if count > 0:
                    return count
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid number.")

    def overclock_node(self, nodes: Dict[int, ResourceNode]) -> None:
        """
        Allow the user to select a node and set its clock speed.

        Args:
            nodes (Dict[int, ResourceNode]): A dictionary of available nodes.
        """
        if not nodes:
            print("No nodes available to overclock.")
            return

        node = self.select_node(nodes)
        if node is None:
            return

        print(f"Current clock speed for node {node.node_id}: {node.clock_speed:.2f}%")
        new_clock_speed = self.get_clock_speed_input()
        node.set_clock_speed(new_clock_speed)
        print(f"Node {node.node_id} clock speed updated to {new_clock_speed:.2f}%")

    def toggle_facility_state(self, facilities: Dict[int, Facility]) -> None:
        """
        Allow the user to toggle the active state of a facility.

        Args:
            facilities (Dict[int, Facility]): A dictionary of available facilities.
        """
        if not facilities:
            print("No facilities available.")
            return

        # Ensure all facilities have the is_active attribute
        for facility in facilities.values():
            if not hasattr(facility, 'is_active'):
                facility.is_active = True

        headers = ["ID", "Type", "Recipe", "Clock Speed", "State"]
        table_data = [
            [facility.facility_id, facility.facility_type, facility.recipe, 
             f"{facility.clock_speed:.1f}%", "On" if facility.is_active else "Off"]
            for facility in facilities.values()
        ]
        
        # Sort the table data by the "Type" column (index 1)
        table_data.sort(key=lambda x: x[1])
        
        print(tabulate(table_data, headers=headers, tablefmt="plain"))
        
        while True:
            choice = input("Enter the ID of the facility to toggle (or 'cancel' to go back): ")
            if choice.lower() == 'cancel':
                return
            try:
                facility_id = int(choice)
                if facility_id in facilities:
                    facility = facilities[facility_id]
                    facility.toggle_active_state()
                    new_state = "on" if facility.is_active else "off"
                    print(f"Facility {facility_id} ({facility.facility_type}) turned {new_state}.")
                    return
                else:
                    print("Invalid facility ID. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or 'cancel'.")

    def display_facility_management_menu(self) -> str:
        """
        Display the facility management menu and return the user's choice.

        Returns:
            str: The selected menu option.
        """
        options = ["Add New Facility", "Add Multiple Facilities", "Edit Facility", 
                   "Toggle Facility State", "Delete Facility", "Return to Main Menu"]
        return self.display_menu("Facility Management", options)

