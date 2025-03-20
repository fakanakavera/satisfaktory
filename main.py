import blessed
from models import ResourceNode, Facility, Base, GameData
from production_graph import ProductionGraph
from ui import UserInterface
from collections import defaultdict
import pickle
import os
from typing import Dict, Any
import json
from tabulate import tabulate
from models import Recipe

class SatisfactoryProductionTracker:
    def __init__(self):
        """
        Initialize the SatisfactoryProductionTracker with necessary components.
        """
        self.term: blessed.Terminal = blessed.Terminal()
        self.filename: str = "satisfactory_tracker_data.pickle"
        self.game_data: GameData = GameData()
        self.ui: UserInterface = UserInterface(self.term, self.game_data)
        self.production_graph: ProductionGraph = ProductionGraph()
        self.load_data()

    def load_data(self) -> None:
        """
        Load saved game data and production graph from a file if it exists.
        """
        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                data: Dict[str, Any] = pickle.load(f)
            self.game_data = data['game_data']
            self.production_graph = data['production_graph']
            self.ui.game_data = self.game_data
            print("Data loaded successfully.")
        else:
            print("No saved data found. Starting with a new session.")

    def prepare_json_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the data for JSON serialization by converting complex objects to dictionaries.

        Args:
            data (Dict[str, Any]): The original data dictionary.

        Returns:
            Dict[str, Any]: A JSON-serializable version of the data.
        """
        json_data = {
            'game_data': {
                'resource_types': [rt.__dict__ for rt in self.game_data.resource_types],
                'miner_types': [mt.__dict__ for mt in self.game_data.miner_types],
                'building_types': [bt.__dict__ for bt in self.game_data.building_types],
                'recipes': [self.recipe_to_dict(recipe) for recipe in self.game_data.recipes],
                'next_base_id': self.game_data.next_base_id,
                'next_node_id': self.game_data.next_node_id,
                'next_facility_id': self.game_data.next_facility_id
            },
            'production_graph': {
                'bases': {base_id: self.base_to_dict(base) for base_id, base in self.production_graph.bases.items()},
                'unlinked_nodes': {node_id: self.node_to_dict(node) for node_id, node in self.production_graph.unlinked_nodes.items()}
            }
        }
        return json_data

    def recipe_to_dict(self, recipe: Recipe) -> Dict[str, Any]:
        """
        Convert a Recipe object to a dictionary.

        Args:
            recipe (Recipe): The Recipe object to convert.

        Returns:
            Dict[str, Any]: A dictionary representation of the Recipe.
        """
        return {
            'name': recipe.name,
            'building_type': recipe.building_type,
            'inputs': recipe.inputs,
            'outputs': recipe.outputs
        }

    def base_to_dict(self, base: Base) -> Dict[str, Any]:
        """
        Convert a Base object to a dictionary.

        Args:
            base (Base): The Base object to convert.

        Returns:
            Dict[str, Any]: A dictionary representation of the Base.
        """
        return {
            'base_id': base.base_id,
            'name': base.name,
            'nodes': {node_id: self.node_to_dict(node) for node_id, node in base.nodes.items()},
            'facilities': {facility_id: self.facility_to_dict(facility) for facility_id, facility in base.facilities.items()},
            'storage': base.storage
        }

    def node_to_dict(self, node: ResourceNode) -> Dict[str, Any]:
        """
        Convert a ResourceNode object to a dictionary.

        Args:
            node (ResourceNode): The ResourceNode object to convert.

        Returns:
            Dict[str, Any]: A dictionary representation of the ResourceNode.
        """
        return {
            'node_id': node.node_id,
            'resource_type': node.resource_type,
            'purity': node.purity,
            'miner_type': node.miner_type,
            'miner_rate': node.miner_rate,
            'output_rate': node.output_rate
        }

    def facility_to_dict(self, facility: Facility) -> Dict[str, Any]:
        """
        Convert a Facility object to a dictionary.

        Args:
            facility (Facility): The Facility object to convert.

        Returns:
            Dict[str, Any]: A dictionary representation of the Facility.
        """
        return {
            'facility_id': facility.facility_id,
            'facility_type': facility.facility_type,
            'recipe': facility.recipe,
            'input_items': facility.input_items,
            'output_items': facility.output_items,
            'clock_speed': facility.clock_speed
        }

    def save_data(self) -> None:
        """
        Save the current game data and production graph to a pickle file and a JSON file.
        """
        data: Dict[str, Any] = {
            'game_data': self.game_data,
            'production_graph': self.production_graph
        }
        
        # Save to pickle file
        with open(self.filename, 'wb') as f:
            pickle.dump(data, f)
        print("Data saved successfully to pickle file.")

        # Save to JSON file for debugging
        json_filename = "satisfactory_tracker_debug.json"
        json_data = self.prepare_json_data(data)
        with open(json_filename, 'w') as f:
            json.dump(json_data, f, indent=2)
        print(f"Debug data saved to {json_filename}")

    def run(self) -> None:
        """
        Run the main loop of the application, displaying the menu and handling user choices.
        """
        while True:
            print(self.term.clear)  # Clear the screen before displaying the menu
            print(self.term.bold_green + self.term.center("=== Satisfactory Production Tracker ==="))
            print(self.term.normal)  # Reset text formatting
            
            choice = self.ui.display_menu("Main Menu", 
                ["Manage Game Data", "Manage Bases", "Manage Nodes", "Track Facilities", 
                 "View Production Rates", "View Net Production", "Identify Bottlenecks", 
                 "Recipe Production Planner", "Save Data", "Exit"],  # Added "Recipe Production Planner"
                allow_escape=False)
            
            if choice == "Manage Game Data":
                self.manage_game_data()
            elif choice == "Manage Bases":
                self.manage_bases()
            elif choice == "Manage Nodes":
                self.manage_nodes()
            elif choice == "Track Facilities":
                self.track_facilities()
            elif choice == "View Production Rates":
                self.view_production_rates()
            elif choice == "View Net Production":
                self.view_net_production()
            elif choice == "Identify Bottlenecks":
                self.identify_bottlenecks()
            elif choice == "Recipe Production Planner":
                self.recipe_production_planner()
            elif choice == "Save Data":
                self.save_data()
            elif choice == "Exit":
                self.save_data()
                break

    def manage_game_data(self) -> None:
        """
        Handle the game data management menu and user choices.
        """
        while True:
            choice = self.ui.display_game_data_menu()
            if choice == "ESC":
                break
            elif choice == "Manage Resource Types":
                self.ui.manage_resource_types()
            elif choice == "Manage Miner Types":
                self.ui.manage_miner_types()
            elif choice == "Manage Building Types":
                self.ui.manage_building_types()
            elif choice == "Manage Recipes":
                self.ui.manage_recipes()
            elif choice == "Return to Main Menu":
                break
        # Save game data after any changes
        self.save_data()

    def manage_bases(self) -> None:
        """
        Handle the base management menu and user choices.
        """
        while True:
            choice = self.ui.display_base_management_menu()
            if choice == "ESC":
                break
            elif choice == "Add New Base":
                base_id, name = self.ui.get_base_input()
                new_base = Base(base_id, name)
                self.production_graph.add_base(new_base)
                print(f"Base '{name}' (ID: {base_id}) added successfully.")
                print(f"Debug: Total bases after adding: {len(self.production_graph.bases)}")
            elif choice == "View All Bases":
                self.view_all_bases()
            elif choice == "Delete Base":
                self.delete_base()
            elif choice == "Return to Main Menu":
                break

    def view_all_bases(self) -> None:
        """
        Display information about all bases, including their nodes and facilities.
        """
        print(f"Debug: Total bases before viewing: {len(self.production_graph.bases)}")
        if not self.production_graph.bases:
            print("No bases have been added yet.")
        else:
            print("\nAll Bases:")
            for base_id, base in self.production_graph.bases.items():
                print(f"ID: {base_id}, Name: {base.name}")
                
                # Group nodes by resource type and calculate total production
                node_summary = defaultdict(lambda: {'count': 0, 'production': 0})
                for node in base.nodes.values():
                    node_summary[node.resource_type]['count'] += 1
                    node_summary[node.resource_type]['production'] += node.output_rate
                
                # Display node summary sorted by resource type
                print(f"  Nodes: {len(base.nodes)}")
                for resource_type in sorted(node_summary.keys()):
                    data = node_summary[resource_type]
                    print(f"    {resource_type}: {data['count']} ({data['production']:.2f}/min)")
                
                # Group facilities by type and calculate total production/consumption
                facility_summary = defaultdict(lambda: {'count': 0, 'input': defaultdict(float), 'output': defaultdict(float)})
                for facility in base.facilities.values():
                    facility_summary[facility.facility_type]['count'] += 1
                    for item, rate in facility.input_items:
                        facility_summary[facility.facility_type]['input'][item] += rate
                    for item, rate in facility.output_items:
                        facility_summary[facility.facility_type]['output'][item] += rate
                
                # Display facility summary sorted by facility type
                print(f"  Facilities: {len(base.facilities)}")
                for facility_type in sorted(facility_summary.keys()):
                    data = facility_summary[facility_type]
                    print(f"    {facility_type}: {data['count']}")
                    print(f"      Inputs:")
                    for item in sorted(data['input'].keys()):
                        rate = data['input'][item]
                        print(f"        {item}: {rate:.2f}/min")
                    print(f"      Outputs:")
                    for item in sorted(data['output'].keys()):
                        rate = data['output'][item]
                        print(f"        {item}: {rate:.2f}/min")
                
                print()
        
        # Add a pause to keep the information on screen
        input("Press Enter to continue...")

    def manage_nodes(self) -> None:
        """
        Handle the node management menu and user choices.
        """
        while True:
            choice = self.ui.display_node_management_menu()
            if choice == "ESC":
                break
            elif choice == "Add New Node":
                self.add_new_node()
            elif choice == "Link Existing Node to Base":
                self.link_node_to_base()
            elif choice == "Overclock Node":
                all_nodes = {**self.production_graph.unlinked_nodes, 
                             **{node.node_id: node for base in self.production_graph.bases.values() for node in base.nodes.values()}}
                self.ui.overclock_node(all_nodes)
            elif choice == "Delete Node":
                self.delete_node()
            elif choice == "Return to Main Menu":
                break

    def add_new_node(self) -> None:
        """
        Add a new resource node to the production graph or a specific base.
        """
        node_id, resource_type, purity, miner_type, miner_rate = self.ui.get_node_input()
        new_node = ResourceNode(node_id, resource_type, purity, miner_type, miner_rate)
        
        if not self.production_graph.bases:
            self.production_graph.add_unlinked_node(new_node)
            print(f"No bases available. Node '{node_id}' added as an unlinked node.")
        else:
            base_id = self.ui.select_base(self.production_graph.bases)
            if base_id is not None:
                if base_id in self.production_graph.bases:
                    self.production_graph.bases[base_id].add_node(new_node)
                    print(f"Node '{node_id}' added to base '{base_id}' successfully.")
                else:
                    print(f"Error: Base with ID {base_id} not found. Adding node as unlinked.")
                    self.production_graph.add_unlinked_node(new_node)
            else:
                self.production_graph.add_unlinked_node(new_node)
                print(f"Node '{node_id}' added as an unlinked node.")

    def link_node_to_base(self) -> None:
        """
        Link an unlinked node to a specific base.
        """
        unlinked_nodes = self.production_graph.get_unlinked_nodes()
        if not unlinked_nodes:
            print("No unlinked nodes available.")
            return

        node = self.ui.select_node(unlinked_nodes)
        if not node:
            return

        base_id = self.ui.select_base(self.production_graph.bases)
        if base_id:
            self.production_graph.bases[base_id].add_node(node)
            self.production_graph.remove_unlinked_node(node)
            print(f"Node '{node.node_id}' linked to base '{base_id}' successfully.")
        else:
            print("No base selected. Node remains unlinked.")

    def track_facilities(self) -> None:
        """
        Handle the facility tracking menu and user choices.
        """
        if not self.production_graph.bases:
            print("No bases available. Please create a base first.")
            return

        base_id = self.ui.select_base(self.production_graph.bases)
        if not base_id:
            print("No base selected. Facility not added.")
            return

        while True:
            choice = self.ui.display_facility_management_menu()
            if choice == "Add New Facility":
                new_facility = self.ui.get_facility_input()
                self.production_graph.bases[base_id].add_facility(new_facility)
                print(f"Facility '{new_facility.facility_id}' added to base '{base_id}' successfully.")
                self.ui.display_facility_details(new_facility)
            elif choice == "Add Multiple Facilities":
                self.add_multiple_facilities(base_id)
            elif choice == "Edit Facility":
                self.edit_facility(base_id)
            elif choice == "Toggle Facility State":
                self.ui.toggle_facility_state(self.production_graph.bases[base_id].facilities)
            elif choice == "Delete Facility":
                self.delete_facility()
            elif choice == "Return to Main Menu":
                break

        # Save game data after any changes
        self.save_data()

    def add_multiple_facilities(self, base_id: int) -> None:
        """
        Add multiple facilities of the same type and recipe to a base.

        Args:
            base_id (int): The ID of the base to add facilities to.
        """
        facility_type = self.ui.select_from_list("Select facility type", [bt.name for bt in self.game_data.building_types])
        recipe = self.ui.select_recipe(self.game_data.recipes, facility_type)
        
        if not recipe:
            print("No recipe selected. Facilities not added.")
            return

        while True:
            try:
                count = int(input("Enter the number of facilities to add: "))
                if count > 0:
                    break
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid number.")

        for _ in range(count):
            facility_id = self.game_data.get_next_facility_id()
            new_facility = Facility(facility_id, facility_type, recipe.name)
            
            for item, rate in recipe.inputs:
                new_facility.set_input_item(item, rate)
            
            for item, rate in recipe.outputs:
                new_facility.set_output_item(item, rate)
            
            self.production_graph.bases[base_id].add_facility(new_facility)

        print(f"{count} facilities of type '{facility_type}' with recipe '{recipe.name}' added to base '{base_id}' successfully.")

    def edit_facility(self, base_id: int) -> None:
        """
        Edit an existing facility in the specified base.

        Args:
            base_id (int): The ID of the base containing the facility to edit.
        """
        facilities = self.production_graph.bases[base_id].facilities
        facility_id = self.ui.select_facility(facilities)
        if facility_id is None:
            return

        facility = facilities[facility_id]
        edit_choice = self.ui.display_menu("Edit Facility", ["Change Recipe", "Change Clock Speed", "Cancel"])
        
        if edit_choice == "Change Recipe":
            new_recipe = self.ui.select_recipe(self.game_data.recipes, facility.facility_type)
            if new_recipe:
                facility.update_recipe(new_recipe)
                print(f"Facility '{facility_id}' recipe updated successfully.")
        elif edit_choice == "Change Clock Speed":
            new_clock_speed = self.ui.get_clock_speed_input()
            facility.set_clock_speed(new_clock_speed)
            print(f"Facility '{facility_id}' clock speed updated to {new_clock_speed}%.")
        
        self.ui.display_facility_details(facility)

    def view_production_rates(self) -> None:
        """
        Display the production rates, consumption rates, and limiting factors for all resources.
        """
        production, consumption, limiting_factors = self.production_graph.calculate_production_rates()
        if not production and not consumption:
            print(self.term.clear + "No production or consumption data available.")
        else:
            print(self.term.clear)  # Clear the screen before displaying data
            self.ui.display_production_rates(production, consumption, limiting_factors)
        input("Press Enter to continue...")  # Add this line to pause the screen

    def view_net_production(self) -> None:
        """
        Display the net production for a selected base.
        """
        self.ui.display_net_production(self.production_graph.bases, self.production_graph)

    def identify_bottlenecks(self) -> None:
        """
        Identify and display resource bottlenecks in the production graph.
        """
        bottlenecks = self.production_graph.identify_bottlenecks()
        if not bottlenecks:
            print(self.term.clear + "No bottlenecks identified.")
        else:
            print(self.term.clear)  # Clear the screen before displaying data
            self.ui.display_bottlenecks(bottlenecks)
        input("Press Enter to continue...")  # Add this line to pause the screen

    def calculate_production_and_consumption(self):
        """
        Calculate and return the total production and consumption rates for all resources.

        Returns:
            Tuple[Dict[str, float], Dict[str, float]]: A tuple containing dictionaries of production and consumption rates.
        """
        production, consumption, _ = self.production_graph.calculate_production_rates()
        return production, consumption

    def delete_base(self) -> None:
        """
        Delete a base from the production graph based on user input.
        """
        base_id = self.ui.delete_base(self.production_graph.bases)
        if base_id:
            self.production_graph.delete_base(base_id)
            print(f"Base with ID {base_id} deleted successfully.")

    def delete_node(self) -> None:
        """
        Delete a node from the production graph based on user input.
        """
        node_id = self.ui.delete_node({**self.production_graph.unlinked_nodes, **{node.node_id: node for base in self.production_graph.bases.values() for node in base.nodes.values()}})
        if node_id:
            self.production_graph.delete_node(node_id)
            print(f"Node with ID {node_id} deleted successfully.")

    def delete_facility(self) -> None:
        """
        Delete a facility from a specific base in the production graph based on user input.
        """
        base_id = self.ui.select_base(self.production_graph.bases)
        if base_id:
            facility_id = self.ui.delete_facility(self.production_graph.bases[base_id].facilities)
            if facility_id:
                self.production_graph.delete_facility(base_id, facility_id)
                print(f"Facility with ID {facility_id} deleted successfully from base {base_id}.")

    def recipe_production_planner(self) -> None:
        """
        Allow the user to select a base and a recipe, then show the net production for the required items.
        """
        if not self.production_graph.bases:
            print("No bases available. Please create a base first.")
            input("Press Enter to continue...")
            return

        base_id = self.ui.select_base(self.production_graph.bases)
        if base_id is None:
            return

        base = self.production_graph.bases[base_id]
        recipe = self.ui.select_recipe(self.game_data.recipes, None)  # Pass None to allow selection from all recipes
        if recipe is None:
            return

        production, consumption = self.production_graph.calculate_production_rates_for_base(base_id)
        net_production = {item: production.get(item, 0) - consumption.get(item, 0) for item in set(production) | set(consumption)}

        print(f"\nRecipe: {recipe.name}")
        print("Required items and their net production:")

        table_data = []
        for item, quantity in recipe.inputs:
            available = net_production.get(item, 0)
            deficit = available - quantity
            status = "Sufficient" if deficit >= 0 else "Insufficient"
            table_data.append([item, f"{available:.2f}", f"{quantity:.2f}", f"{deficit:.2f}", status])

        headers = ["Item", "Available", "Required", "Net", "Status"]
        print(tabulate(table_data, headers=headers, tablefmt="plain"))

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    app = SatisfactoryProductionTracker()
    app.run()
