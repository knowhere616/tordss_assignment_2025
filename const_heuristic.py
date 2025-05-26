from Parser import *

class Fcvrp:
    def __init__(self, filename, truck_capacity=400, max_trucks=3):
        self.filename = filename
        self.costs = []
        self.group_demands = {}
        self.group_sizes = [9, 9, 10, 4, 5, 8, 6, 11, 4, 13]
        self.group_unit_demands = [13, 14, 17, 13, 14, 18, 11, 16, 13, 16]
        self.visited_group_sizes = [12, 9, 10, 5, 5, 8, 6, 17, 5, 23]
        self.visited = []
        self.model = None
        self.TRUCK_CAPACITY = truck_capacity
        self.MAX_TRUCKS = max_trucks
        self.trucks_used = 0
        self.current_truck_capacity = 0
        self.truck_routes = [[] for _ in range(self.MAX_TRUCKS)]
        self.solution = []  

        self.load_model()
        self.load_costs()
        self.calculate_group_demands()
        self.initialize_visited()

    def load_model(self):
        self.model = load_model(self.filename)

    def load_costs(self):
        with open(self.filename, "r", encoding="utf-8") as file:
            lines = file.readlines()
        data_lines = lines[4:104]

        for line in data_lines:
            row = list(map(int, line.strip().split()))
            self.costs.append(row)

    def calculate_group_demands(self):
        for group_id, (size, unit_demand) in enumerate(zip(self.group_sizes, self.group_unit_demands)):
            self.group_demands[group_id] = size * unit_demand

        self.group_demands = {k: v for k, v in sorted(self.group_demands.items(), key=lambda item: item[1], reverse=True)}

    def initialize_visited(self):
        self.visited = [[False for _ in range(100)] for size in self.visited_group_sizes]

    def visit_nodes(self):
        print("\n--- Visiting Nodes by Truck ---")
        for group_id in self.group_demands:
            print()
            demand_per_node = self.group_unit_demands[group_id]
            max_to_visit = self.group_sizes[group_id]
            visited_count = 0

            print(f"\nGroup {self.model.families[group_id].id} (Visit {max_to_visit} nodes, Demand per node = {demand_per_node}):")

            for node_index in range(len(self.visited[group_id])):
                if visited_count >= max_to_visit:
                    break

                while True:
                    if self.trucks_used >= self.MAX_TRUCKS:
                        print("❌ No more trucks available. Ending route planning.")
                        self.build_solution()  
                        return

                    if self.current_truck_capacity + demand_per_node <= self.TRUCK_CAPACITY:
                        self.current_truck_capacity += demand_per_node
                        print()
                        node_id = int(self.model.families[group_id].nodes[node_index].id)
                        self.visited[int(self.model.families[group_id].id)][node_id] = True
                        visited_count += 1
                        self.truck_routes[self.trucks_used].append(node_id)
                        print(f"  ✅ Node {node_id} visited (Truck {self.trucks_used}, Load: {self.current_truck_capacity}/{self.TRUCK_CAPACITY})")
                        break

                    self.switch_truck(group_id, node_index)

                    if self.trucks_used >= self.MAX_TRUCKS:
                        break

        self.build_solution()  

    def switch_truck(self, group_id, node_index):
        self.trucks_used += 1
        if self.trucks_used >= self.MAX_TRUCKS:
            print(f"  🚫 Node {self.model.families[group_id].nodes[node_index].id} cannot be visited (no trucks left)")
            return
        self.current_truck_capacity = 0
        print(f"  🔁 Switching to Truck {self.trucks_used} for Node {self.model.families[group_id].nodes[node_index].id}...")

    def build_solution(self):
        self.solution = [route for route in self.truck_routes if route]



if __name__ == "__main__":
    fcvrp_instance = Fcvrp("fcvrp_P-n101-k4_10_3_3.txt")
    fcvrp_instance.visit_nodes()
    