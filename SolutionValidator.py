def validate_solution(model, routes):
    """
    Validates if the given routes form a valid solution for the CVPR problem.

    Args:
        model: The problem model object
        routes: A list of lists, where each inner list represents a route
                (sequence of node IDs visited by a vehicle)

    Returns:
        valid: Boolean indicating if the solution is valid
        validation_report: Dictionary containing validation details and errors if any
    """
    validation_report = {
        "valid": True,
        "total_cost": 0,
        "errors": [],
        "route_loads": [],
        "route_costs": [],
        "family_visits": {},
    }

    # Initialize family visits counter
    for family in model.families:
        validation_report["family_visits"][family.id] = 0

    # Check number of vehicles
    if len(routes) > model.vehicles:
        validation_report["valid"] = False
        validation_report["errors"].append(f"Too many vehicles used: {len(routes)} > {model.vehicles}")

    # Check each route
    visited_nodes = set()

    for route_idx, route in enumerate(routes):
        route_load = 0
        route_cost = 0
        prev_node_id = 0  # Start at depot

        # Check if route starts and ends at depot
        if route[0] != 0 or route[-1] != 0:
            validation_report["valid"] = False
            validation_report["errors"].append(f"Route {route_idx} doesn't start or end at depot: {route}")

        # Check intermediate nodes
        for i in range(1, len(route) - 1):
            node_id = route[i]

            # Check if node ID is valid
            if node_id < 0 or node_id > model.num_nodes:
                validation_report["valid"] = False
                validation_report["errors"].append(f"Invalid node ID in route {route_idx}: {node_id}")
                continue

            if node_id in visited_nodes:
                validation_report["valid"] = False
                validation_report["errors"].append(f"Node {node_id} visited multiple times")
                continue

            visited_nodes.add(node_id)

            # Update family visits counter
            node = model.nodes[node_id]
            if node.family is not None:
                validation_report["family_visits"][node.family] += 1

            # Update route load
            if node.demand is not None:
                route_load += node.demand

            # Update route cost
            route_cost += model.cost_matrix[prev_node_id][node_id]
            prev_node_id = node_id

        # Add cost of returning to depot
        if len(route) > 1:
            last_node_id = route[-2]
            route_cost += model.cost_matrix[last_node_id][0]

        # Check if route exceeds vehicle capacity
        if route_load > model.capacity:
            validation_report["valid"] = False
            validation_report["errors"].append(f"Route {route_idx} exceeds capacity: {route_load} > {model.capacity}")

        validation_report["route_loads"].append(route_load)
        validation_report["route_costs"].append(route_cost)
        validation_report["total_cost"] += route_cost

    # Check if required visits for each family are satisfied
    for family in model.families:
        if validation_report["family_visits"][family.id] < family.required_visits:
            validation_report["valid"] = False
            validation_report["errors"].append(
                f"Family {family.id} has insufficient visits: "
                f"{validation_report['family_visits'][family.id]} < {family.required_visits}"
            )

    return validation_report["valid"], validation_report


def parse_solution_file(solution_file):
    """
    Parse a solution file into a list of routes.

    Args:
        solution_file: Path to the solution file

    Returns:
        routes: List of routes, where each route is a list of node IDs
    """
    routes = []

    with open(solution_file, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line.strip():
            route = list(map(int, line.strip().split()))
            routes.append(route)

    return routes