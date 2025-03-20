from typing import Dict, Tuple, List
from models import Base, ResourceNode
from decimal import Decimal, ROUND_HALF_UP

class ProductionGraph:
    def __init__(self):
        """
        Initialize a new ProductionGraph instance.
        """
        self.bases: Dict[int, Base] = {}
        self.unlinked_nodes: Dict[int, ResourceNode] = {}

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

    def add_base(self, base: Base) -> None:
        """
        Add a base to the production graph.

        Args:
            base (Base): The base to be added.
        """
        self.bases[base.base_id] = base

    def calculate_production_rates(self) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, List[str]]]:
        """
        Calculate the production rates, consumption rates, and limiting factors for all resources in the graph.

        Returns:
            Tuple[Dict[str, float], Dict[str, float], Dict[str, List[str]]]: A tuple containing:
                - total_production: A dictionary of resource types and their total production rates.
                - total_consumption: A dictionary of resource types and their total consumption rates.
                - limiting_factors: A dictionary of resource types and lists of their limiting input resources.
        """
        raw_production: Dict[str, float] = {}
        total_production: Dict[str, float] = {}
        total_consumption: Dict[str, float] = {}
        limiting_factors: Dict[str, List[str]] = {}

        # Calculate raw production from nodes
        for base in self.bases.values():
            for node in base.nodes.values():
                raw_production[node.resource_type] = self.round_float(raw_production.get(node.resource_type, 0) + node.output_rate, 2)

        # Include production from unlinked nodes
        for node in self.unlinked_nodes.values():
            raw_production[node.resource_type] = self.round_float(raw_production.get(node.resource_type, 0) + node.output_rate, 2)

        # Initialize total_production with raw_production
        total_production = raw_production.copy()

        # Calculate consumption and production for facilities
        for base in self.bases.values():
            for facility in base.facilities.values():
                adjusted_inputs, adjusted_outputs = facility.get_adjusted_rates()
                
                for item, rate in adjusted_inputs:
                    total_consumption[item] = self.round_float(total_consumption.get(item, 0) + rate, 2)

                for item, rate in adjusted_outputs:
                    total_production[item] = self.round_float(total_production.get(item, 0) + rate, 2)

        # Identify limiting factors and adjust production
        for item, consumption in total_consumption.items():
            if consumption > total_production.get(item, 0):
                production_ratio = self.round_float(total_production.get(item, 0) / consumption, 4)
                limiting_factors[item] = []

                # Adjust production of items that use this as input
                for base in self.bases.values():
                    for facility in base.facilities.values():
                        adjusted_inputs, adjusted_outputs = facility.get_adjusted_rates()
                        if any(input_item == item for input_item, _ in adjusted_inputs):
                            for output_item, output_rate in adjusted_outputs:
                                total_production[output_item] = self.round_float(total_production[output_item] - output_rate * (1 - production_ratio), 2)
                                if output_item not in limiting_factors:
                                    limiting_factors[output_item] = []
                                limiting_factors[output_item].append(item)

        return total_production, total_consumption, limiting_factors

    def identify_bottlenecks(self) -> Dict[str, float]:
        """
        Identify resource bottlenecks in the production graph.

        Returns:
            Dict[str, float]: A dictionary of resource types and their deficit amounts (consumption rate - production rate).
        """
        production, consumption = self.calculate_production_rates()
        bottlenecks: Dict[str, float] = {}

        for item in set(production.keys()) | set(consumption.keys()):
            prod_rate = production.get(item, 0)
            cons_rate = consumption.get(item, 0)
            deficit = self.round_float(cons_rate - prod_rate, 2)
            if deficit > 0:
                bottlenecks[item] = deficit

        return bottlenecks

    def add_unlinked_node(self, node: ResourceNode) -> None:
        """
        Add an unlinked resource node to the production graph.

        Args:
            node (ResourceNode): The resource node to be added.
        """
        self.unlinked_nodes[node.node_id] = node

    def remove_unlinked_node(self, node: ResourceNode) -> None:
        """
        Remove an unlinked resource node from the production graph.

        Args:
            node (ResourceNode): The resource node to be removed.
        """
        self.unlinked_nodes.pop(node.node_id, None)

    def get_unlinked_nodes(self) -> Dict[int, ResourceNode]:
        """
        Get all unlinked resource nodes in the production graph.

        Returns:
            Dict[int, ResourceNode]: A dictionary of node IDs and their corresponding ResourceNode objects.
        """
        return self.unlinked_nodes

    def delete_base(self, base_id: int) -> None:
        """
        Delete a base from the production graph.

        Args:
            base_id (int): The ID of the base to be deleted.
        """
        if base_id in self.bases:
            del self.bases[base_id]

    def delete_node(self, node_id: int) -> None:
        """
        Delete a resource node from the production graph.

        Args:
            node_id (int): The ID of the node to be deleted.
        """
        for base in self.bases.values():
            if node_id in base.nodes:
                del base.nodes[node_id]
                return
        if node_id in self.unlinked_nodes:
            del self.unlinked_nodes[node_id]

    def delete_facility(self, base_id: int, facility_id: int) -> None:
        """
        Delete a facility from a specific base in the production graph.

        Args:
            base_id (int): The ID of the base containing the facility.
            facility_id (int): The ID of the facility to be deleted.
        """
        if base_id in self.bases and facility_id in self.bases[base_id].facilities:
            del self.bases[base_id].facilities[facility_id]

    def calculate_production_rates_for_base(self, base_id: int) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Calculate the production rates and consumption rates for a specific base.

        Args:
            base_id (int): The ID of the base to calculate rates for.

        Returns:
            Tuple[Dict[str, float], Dict[str, float]]: A tuple containing:
                - production: A dictionary of resource types and their production rates.
                - consumption: A dictionary of resource types and their consumption rates.
        """
        production: Dict[str, float] = {}
        consumption: Dict[str, float] = {}

        if base_id not in self.bases:
            return production, consumption

        base = self.bases[base_id]

        # Calculate production from nodes in the base
        for node in base.nodes.values():
            production[node.resource_type] = self.round_float(production.get(node.resource_type, 0) + node.output_rate, 2)

        # Calculate consumption and production for facilities in the base
        for facility in base.facilities.values():
            adjusted_inputs, adjusted_outputs = facility.get_adjusted_rates()
            
            for item, rate in adjusted_inputs:
                consumption[item] = self.round_float(consumption.get(item, 0) + rate, 2)

            for item, rate in adjusted_outputs:
                production[item] = self.round_float(production.get(item, 0) + rate, 2)

        return production, consumption
