from dataclasses import dataclass
from typing import List


@dataclass
class Node:
    id: int
    family: int
    costs: List[int]
    demand: int
    isDepot: bool = False


@dataclass
class Family:
    id: int
    nodes: List[Node]
    demand: int
    required_visits: int


@dataclass
class Model:
    num_nodes: int = 0
    num_fam: int = 0
    num_req: int = 0
    capacity: int = 0
    vehicles: int = 0
    fam_members: List[int] = None
    fam_req: List[int] = None
    fam_dem: List[int] = None
    cost_matrix: List[List[int]] = None
    families: List[Family] = None
    nodes: List[Node] = None
    customers: List[Node] = None
    depot: Node = None


def load_model(file_name):
    """
    Parse the CVPR problem instance from a file.
    Format:
    1st line: |N| L V Q K (num_nodes, num_families, num_required, capacity, vehicles)
    2nd line: List of family members (nl)
    3rd line: List of family visits (vl)
    4th line: List of family demands (dl)
    5th line until end: Cost matrix (cij)
    """

    parsed_model = Model()
    all_lines = list(open(file_name, "r"))
    line_counter = 0

    # 1st line: |N| L V Q K
    ln = all_lines[line_counter]
    no_spaces = ln.split()

    parsed_model.num_nodes = int(no_spaces[0])
    parsed_model.num_fam = int(no_spaces[1])
    parsed_model.num_req = int(no_spaces[2])
    parsed_model.capacity = int(no_spaces[3])
    parsed_model.vehicles = int(no_spaces[4])

    # 2nd line: List of family members (nl)
    line_counter += 1
    ln = all_lines[line_counter]
    parsed_model.fam_members = list(map(int, ln.split()))

    # 3rd line: List of family visits (vl)
    line_counter += 1
    ln = all_lines[line_counter]
    parsed_model.fam_req = list(map(int, ln.split()))

    # 4th line: List of family demands (dl)
    line_counter += 1
    ln = all_lines[line_counter]
    parsed_model.fam_dem = list(map(int, ln.split()))

    # 5th line until end: Cost matrix (cij)
    cost_matrix = []
    for i in range(parsed_model.num_nodes + 1):  # +1 for depot
        line_counter += 1
        ln = all_lines[line_counter]
        no_spaces = list(map(int, ln.split()))
        cost_matrix.append(no_spaces)

    parsed_model.cost_matrix = cost_matrix

    # Create node and family objects
    parsed_model = create_nodes_families(parsed_model)

    return parsed_model


def find_position(arr, target):
    """
    Find the position of target in the cumulative sum array
    This is used to determine which family a node belongs to
    """
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return left if left < len(arr) else -1


def create_nodes_families(parsed_model):
    """
    Create Node and Family objects from the parsed data
    """
    families = []
    nodes = []

    # Create Family objects
    for i in range(len(parsed_model.fam_members)):
        family = Family(
            id=i,
            nodes=[],
            demand=parsed_model.fam_dem[i],
            required_visits=parsed_model.fam_req[i]
        )
        families.append(family)

    # Calculate cumulative sum of family members to determine node-to-family mapping
    fam_index = []
    cumulative = 0
    for members in parsed_model.fam_members:
        cumulative += members
        fam_index.append(cumulative)

    # Create Node objects
    for i in range(len(parsed_model.cost_matrix)):
        if i == 0:
            # Depot node
            node = Node(
                id=i,
                family=None,
                costs=parsed_model.cost_matrix[i],
                demand=0
            )
            node.isDepot = True
            parsed_model.depot = node
            nodes.append(node)
        else:
            # Find which family this node belongs to
            family_idx = find_position(fam_index, i)
            node = Node(
                id=i,
                family=family_idx,
                costs=parsed_model.cost_matrix[i],
                demand=families[family_idx].demand
            )
            nodes.append(node)
            families[family_idx].nodes.append(node)

    parsed_model.families = families
    parsed_model.nodes = nodes
    parsed_model.customers = nodes[1:]  # All nodes except depot

    return parsed_model


if __name__ == "__main__":
    model = load_model("fcvrp_P-n101-k4_10_3_3.txt")