import unittest
from models import GameData, Base, ResourceNode, Facility, Recipe
from production_graph import ProductionGraph
from main import SatisfactoryProductionTracker
from ui import UserInterface
import blessed

class TestGameData(unittest.TestCase):
    def setUp(self):
        self.game_data = GameData()

    def test_add_resource_type(self):
        self.game_data.add_resource_type("Iron Ore")
        self.assertEqual(len(self.game_data.resource_types), 1)
        self.assertEqual(self.game_data.resource_types[0].name, "Iron Ore")

    def test_add_miner_type(self):
        self.game_data.add_miner_type("Miner Mk.1", 60)
        self.assertEqual(len(self.game_data.miner_types), 1)
        self.assertEqual(self.game_data.miner_types[0].name, "Miner Mk.1")
        self.assertEqual(self.game_data.miner_types[0].base_rate, 60)

    def test_add_building_type(self):
        self.game_data.add_building_type("Smelter")
        self.assertEqual(len(self.game_data.building_types), 1)
        self.assertEqual(self.game_data.building_types[0].name, "Smelter")

    def test_add_recipe(self):
        self.game_data.add_recipe("Iron Ingot", "Smelter", [("Iron Ore", 30)], [("Iron Ingot", 30)])
        self.assertEqual(len(self.game_data.recipes), 1)
        self.assertEqual(self.game_data.recipes[0].name, "Iron Ingot")

class TestProductionGraph(unittest.TestCase):
    def setUp(self):
        self.production_graph = ProductionGraph()
        self.base = Base(1, "Main Base")
        self.production_graph.add_base(self.base)

    def test_add_base(self):
        self.assertEqual(len(self.production_graph.bases), 1)
        self.assertEqual(self.production_graph.bases[1].name, "Main Base")

    def test_add_node(self):
        node = ResourceNode(1, "Iron Ore", "Normal", "Miner Mk.1", 60)
        self.base.add_node(node)
        self.assertEqual(len(self.base.nodes), 1)
        self.assertEqual(self.base.nodes[1].resource_type, "Iron Ore")

    def test_add_facility(self):
        facility = Facility(1, "Smelter", "Iron Ingot")
        self.base.add_facility(facility)
        self.assertEqual(len(self.base.facilities), 1)
        self.assertEqual(self.base.facilities[1].facility_type, "Smelter")

    def test_calculate_production_rates(self):
        node = ResourceNode(1, "Iron Ore", "Normal", "Miner Mk.1", 60)
        self.base.add_node(node)
        facility = Facility(1, "Smelter", "Iron Ingot")
        facility.set_input_item("Iron Ore", 30)
        facility.set_output_item("Iron Ingot", 30)
        self.base.add_facility(facility)
        
        production, consumption, limiting_factors = self.production_graph.calculate_production_rates()
        self.assertEqual(production["Iron Ore"], 60)
        self.assertEqual(production["Iron Ingot"], 30)
        self.assertEqual(consumption["Iron Ore"], 30)

    def test_node_overclock(self):
        node = ResourceNode(1, "Iron Ore", "Normal", "Miner Mk.1", 60)
        self.base.add_node(node)
        
        # Check initial output rate
        self.assertAlmostEqual(node.output_rate, 60.0, places=2)
        
        # Set clock speed to 150%
        node.set_clock_speed(150.0)
        self.assertAlmostEqual(node.output_rate, 90.0, places=2)
        
        # Set clock speed to 250% (maximum)
        node.set_clock_speed(250.0)
        self.assertAlmostEqual(node.output_rate, 150.0, places=2)
        
        # Set clock speed to 50%
        node.set_clock_speed(50.0)
        self.assertAlmostEqual(node.output_rate, 30.0, places=2)
        
        # Try to set clock speed above maximum (should cap at 250%)
        node.set_clock_speed(300.0)
        self.assertAlmostEqual(node.output_rate, 150.0, places=2)
        
        # Try to set clock speed below minimum (should cap at 0.001%)
        node.set_clock_speed(0.0)
        self.assertAlmostEqual(node.output_rate, 0.0006, places=4)

    def test_facility_overclock(self):
        facility = Facility(1, "Smelter", "Iron Ingot")
        facility.set_input_item("Iron Ore", 30)
        facility.set_output_item("Iron Ingot", 30)
        self.base.add_facility(facility)
        
        # Check initial rates
        self.assertAlmostEqual(facility.get_adjusted_rates()[0][0][1], 30.0, places=6)
        self.assertAlmostEqual(facility.get_adjusted_rates()[1][0][1], 30.0, places=6)
        
        # Set clock speed to 150%
        facility.set_clock_speed(150.0)
        self.assertAlmostEqual(facility.get_adjusted_rates()[0][0][1], 45.0, places=6)
        self.assertAlmostEqual(facility.get_adjusted_rates()[1][0][1], 45.0, places=6)
        
        # Set clock speed to 250% (maximum)
        facility.set_clock_speed(250.0)
        self.assertAlmostEqual(facility.get_adjusted_rates()[0][0][1], 75.0, places=6)
        self.assertAlmostEqual(facility.get_adjusted_rates()[1][0][1], 75.0, places=6)
        
        # Set clock speed to 50%
        facility.set_clock_speed(50.0)
        self.assertAlmostEqual(facility.get_adjusted_rates()[0][0][1], 15.0, places=6)
        self.assertAlmostEqual(facility.get_adjusted_rates()[1][0][1], 15.0, places=6)
        
        # Try to set clock speed above maximum (should cap at 250%)
        facility.set_clock_speed(300.0)
        self.assertAlmostEqual(facility.get_adjusted_rates()[0][0][1], 75.0, places=6)
        self.assertAlmostEqual(facility.get_adjusted_rates()[1][0][1], 75.0, places=6)
        
        # Try to set clock speed below minimum (should cap at 0.001%)
        facility.set_clock_speed(0.0)
        self.assertAlmostEqual(facility.get_adjusted_rates()[0][0][1], 0.0003, places=6)
        self.assertAlmostEqual(facility.get_adjusted_rates()[1][0][1], 0.0003, places=6)

    def test_complex_facilities(self):
        # Add resource nodes
        copper_node1 = ResourceNode(1, "Copper Ore", "Normal", "Miner Mk2", 120)
        copper_node2 = ResourceNode(2, "Copper Ore", "Normal", "Miner Mk2", 120)
        oil_node1 = ResourceNode(3, "Crude Oil", "Normal", "Oil Extractor", 60)
        oil_node2 = ResourceNode(4, "Crude Oil", "Normal", "Oil Extractor", 120)
        oil_node3 = ResourceNode(5, "Crude Oil", "Normal", "Oil Extractor", 120)
        
        for node in [copper_node1, copper_node2, oil_node1, oil_node2, oil_node3]:
            self.base.add_node(node)

        # Add facilities
        # Copper Ingot Smelters
        for i in range(5):
            smelter = Facility(10 + i, "Smelter", "Copper Ingot")
            smelter.set_input_item("Copper Ore", 30)
            smelter.set_output_item("Copper Ingot", 30)
            self.base.add_facility(smelter)

        # Wire Constructors
        wire_constructor1 = Facility(15, "Constructor", "Wire")
        wire_constructor1.set_input_item("Copper Ingot", 15)
        wire_constructor1.set_output_item("Wire", 30)
        self.base.add_facility(wire_constructor1)

        wire_constructor2 = Facility(16, "Constructor", "Wire")
        wire_constructor2.set_input_item("Copper Ingot", 15)
        wire_constructor2.set_output_item("Wire", 30)
        self.base.add_facility(wire_constructor2)

        wire_constructor3 = Facility(17, "Constructor", "Wire")
        wire_constructor3.set_input_item("Copper Ingot", 15)
        wire_constructor3.set_output_item("Wire", 30)
        wire_constructor3.set_clock_speed(66.666666)
        self.base.add_facility(wire_constructor3)

        # Copper Sheet Constructors
        for i in range(4):
            sheet_constructor = Facility(20 + i, "Constructor", "Copper Sheet")
            sheet_constructor.set_input_item("Copper Ingot", 20)
            sheet_constructor.set_output_item("Copper Sheet", 10)
            self.base.add_facility(sheet_constructor)

        # Cable Constructor
        cable_constructor = Facility(24, "Constructor", "Cable")
        cable_constructor.set_input_item("Wire", 60)
        cable_constructor.set_output_item("Cable", 30)
        cable_constructor.set_clock_speed(133.3333333)
        self.base.add_facility(cable_constructor)

        # Plastic Refineries
        plastic_refinery1 = Facility(25, "Refinery", "Plastic")
        plastic_refinery1.set_input_item("Crude Oil", 30)
        plastic_refinery1.set_output_item("Plastic", 20)
        plastic_refinery1.set_output_item("Heavy Oil Residue", 10)
        plastic_refinery1.set_clock_speed(200.0)
        self.base.add_facility(plastic_refinery1)

        plastic_refinery2 = Facility(26, "Refinery", "Plastic")
        plastic_refinery2.set_input_item("Crude Oil", 30)
        plastic_refinery2.set_output_item("Plastic", 20)
        plastic_refinery2.set_output_item("Heavy Oil Residue", 10)
        plastic_refinery2.set_clock_speed(150.0)
        self.base.add_facility(plastic_refinery2)

        plastic_refinery3 = Facility(27, "Refinery", "Plastic")
        plastic_refinery3.set_input_item("Crude Oil", 30)
        plastic_refinery3.set_output_item("Plastic", 20)
        plastic_refinery3.set_output_item("Heavy Oil Residue", 10)
        plastic_refinery3.set_clock_speed(250.0)
        self.base.add_facility(plastic_refinery3)

        # Circuit Board Assembler
        circuit_board_assembler = Facility(28, "Assembler", "Circuit Board")
        circuit_board_assembler.set_input_item("Copper Sheet", 15)
        circuit_board_assembler.set_input_item("Plastic", 30)
        circuit_board_assembler.set_output_item("Circuit Board", 7.5)
        circuit_board_assembler.set_clock_speed(133.33333333)
        self.base.add_facility(circuit_board_assembler)

        # Fuel Refinery
        fuel_refinery = Facility(29, "Refinery", "Residual Fuel")
        fuel_refinery.set_input_item("Heavy Oil Residue", 60)
        fuel_refinery.set_output_item("Fuel", 40)
        self.base.add_facility(fuel_refinery)

        # Computer Manufacturer
        computer_manufacturer = Facility(30, "Manufacturer", "Computer")
        computer_manufacturer.set_input_item("Circuit Board", 10)
        computer_manufacturer.set_input_item("Cable", 20)
        computer_manufacturer.set_input_item("Plastic", 40)
        computer_manufacturer.set_output_item("Computer", 2.5)
        self.base.add_facility(computer_manufacturer)

        # Calculate production rates
        production, consumption, _ = self.production_graph.calculate_production_rates()

        # Verify production rates
        self.assertAlmostEqual(production["Copper Ore"], 240, places=2)
        self.assertAlmostEqual(production["Crude Oil"], 300, places=2)
        self.assertAlmostEqual(production["Copper Ingot"], 150, places=2)
        self.assertAlmostEqual(production["Wire"], 80, places=2)
        self.assertAlmostEqual(production["Copper Sheet"], 40, places=2)
        self.assertAlmostEqual(production["Cable"], 40, places=2)
        self.assertAlmostEqual(production["Plastic"], 120, places=2)
        self.assertAlmostEqual(production["Heavy Oil Residue"], 60, places=2)
        self.assertAlmostEqual(production["Circuit Board"], 10, places=2)
        self.assertAlmostEqual(production["Computer"], 2.5, places=2)
        self.assertAlmostEqual(production["Fuel"], 40, places=2)

        # Verify consumption rates
        self.assertAlmostEqual(consumption["Copper Ore"], 150, places=2)
        self.assertAlmostEqual(consumption["Crude Oil"], 180, places=2)
        self.assertAlmostEqual(consumption["Copper Ingot"], 120, places=2)
        self.assertAlmostEqual(consumption["Wire"], 80, places=2)
        self.assertAlmostEqual(consumption["Copper Sheet"], 20, places=2)
        self.assertAlmostEqual(consumption["Cable"], 20, places=2)
        self.assertAlmostEqual(consumption["Plastic"], 80, places=2)
        self.assertAlmostEqual(consumption["Heavy Oil Residue"], 60, places=2)
        self.assertAlmostEqual(consumption["Circuit Board"], 10, places=2)

        # Test overclocking
        computer_manufacturer.set_clock_speed(50.0)
        production, consumption, _ = self.production_graph.calculate_production_rates()

        # Check updated rates for computer manufacturer
        self.assertAlmostEqual(consumption["Circuit Board"], 5, places=2)
        self.assertAlmostEqual(consumption["Cable"], 10, places=2)
        self.assertAlmostEqual(consumption["Plastic"], 60, places=2)
        self.assertAlmostEqual(production["Computer"], 1.25, places=2)

        # Verify that production still meets or exceeds consumption after overclocking
        for resource in set(production.keys()) | set(consumption.keys()):
            self.assertGreaterEqual(production.get(resource, 0), consumption.get(resource, 0),
                                    f"Production of {resource} does not meet consumption after overclocking")



class TestSatisfactoryProductionTracker(unittest.TestCase):
    def setUp(self):
        self.app = SatisfactoryProductionTracker()

    def test_add_base(self):
        initial_base_count = len(self.app.production_graph.bases)  
        new_base = Base(self.app.game_data.get_next_base_id(), "Test Base")
        self.app.production_graph.add_base(new_base)
        
        final_base_count = len(self.app.production_graph.bases)
        
        self.assertEqual(final_base_count, initial_base_count + 1, 
                         f"Expected {initial_base_count + 1} bases, but got {final_base_count}")

    def test_add_node(self):
        base = Base(self.app.game_data.get_next_base_id(), "Test Base")
        self.app.production_graph.add_base(base)
        node = ResourceNode(self.app.game_data.get_next_node_id(), "Iron Ore", "Normal", "Miner Mk.1", 60)
        base.add_node(node)
        self.assertEqual(len(base.nodes), 1)

    def test_add_facility(self):
        base = Base(self.app.game_data.get_next_base_id(), "Test Base")
        self.app.production_graph.add_base(base)
        facility = Facility(self.app.game_data.get_next_facility_id(), "Smelter", "Iron Ingot")
        base.add_facility(facility)
        self.assertEqual(len(base.facilities), 1)

class TestUserInterface(unittest.TestCase):
    def setUp(self):
        self.game_data = GameData()
        self.term = blessed.Terminal()
        self.ui = UserInterface(self.term, self.game_data)

    def test_calculate_possible_recipes(self):
        # Add resource types
        self.game_data.add_resource_type("Iron Ore")
        self.game_data.add_resource_type("Iron Ingot")
        self.game_data.add_resource_type("Iron Plate")
        self.game_data.add_resource_type("Screw")
        self.game_data.add_resource_type("Copper Ore")
        self.game_data.add_resource_type("Copper Ingot")
        self.game_data.add_resource_type("Wire")
        self.game_data.add_resource_type("Cable")
        self.game_data.add_resource_type("Reinforced Iron Plate")
        self.game_data.add_resource_type("Computer")
        self.game_data.add_resource_type("Circuit Board")
        self.game_data.add_resource_type("Plastic")

        # Add recipes
        self.game_data.add_recipe("Iron Ingot", "Smelter", [("Iron Ore", 30)], [("Iron Ingot", 30)])
        self.game_data.add_recipe("Iron Plate", "Constructor", [("Iron Ingot", 30)], [("Iron Plate", 20)])
        self.game_data.add_recipe("Screw", "Constructor", [("Iron Ingot", 10)], [("Screw", 40)])
        self.game_data.add_recipe("Copper Ingot", "Smelter", [("Copper Ore", 30)], [("Copper Ingot", 30)])
        self.game_data.add_recipe("Wire", "Constructor", [("Copper Ingot", 15)], [("Wire", 30)])
        self.game_data.add_recipe("Cable", "Constructor", [("Wire", 60)], [("Cable", 30)])
        self.game_data.add_recipe("Reinforced Iron Plate", "Assembler", [("Iron Plate", 30), ("Screw", 60)], [("Reinforced Iron Plate", 5)])
        self.game_data.add_recipe("Computer", "Manufacturer", [("Circuit Board", 10), ("Cable", 9), ("Plastic", 18), ("Screw", 52)], [("Computer", 1)])

        # Test case 1: Exact match for one recipe
        net_production = {
            "Iron Ore": 30,
            "Iron Ingot": 0,
            "Iron Plate": 0,
            "Screw": 0
        }
        possible_recipes = self.ui.calculate_possible_recipes(net_production)
        self.assertEqual(possible_recipes, {"Iron Ingot": 1})

        # Test case 2: Multiple recipes possible
        net_production = {
            "Iron Ore": 90,
            "Iron Ingot": 60,
            "Iron Plate": 0,
            "Screw": 0,
            "Copper Ore": 60,
            "Copper Ingot": 30,
            "Wire": 60,
            "Cable": 0
        }
        possible_recipes = self.ui.calculate_possible_recipes(net_production)
        self.assertEqual(possible_recipes, {
            "Iron Ingot": 3,
            "Iron Plate": 2,
            "Screw": 6,
            "Copper Ingot": 2,
            "Wire": 2,
            "Cable": 1
        })

        # Test case 3: No recipes possible
        net_production = {
            "Iron Ore": 15,
            "Iron Ingot": 5,
            "Iron Plate": 0,
            "Screw": 0
        }
        possible_recipes = self.ui.calculate_possible_recipes(net_production)
        self.assertEqual(possible_recipes, {})

        # Test case 4: Complex recipes (Assembler and Manufacturer)
        net_production = {
            "Iron Plate": 60,
            "Screw": 120,
            "Circuit Board": 10,
            "Cable": 9,
            "Plastic": 18,
            "Wire": 60
        }
        possible_recipes = self.ui.calculate_possible_recipes(net_production)
        self.assertEqual(possible_recipes, {
            "Reinforced Iron Plate": 2,
            "Computer": 1,
            "Cable": 1
        })

        # Test case 5: Excess resources with complex recipes
        net_production = {
            "Iron Ore": 200,
            "Iron Ingot": 100,
            "Iron Plate": 80,
            "Screw": 200,
            "Copper Ore": 150,
            "Copper Ingot": 75,
            "Wire": 120,
            "Cable": 20,
            "Circuit Board": 15,
            "Plastic": 30
        }
        possible_recipes = self.ui.calculate_possible_recipes(net_production)
        self.assertEqual(possible_recipes, {
            "Iron Ingot": 6,
            "Iron Plate": 3,
            "Screw": 10,
            "Copper Ingot": 5,
            "Wire": 5,
            "Cable": 2,
            "Reinforced Iron Plate": 2,
            "Computer": 1
        })

if __name__ == '__main__':
    unittest.main()
