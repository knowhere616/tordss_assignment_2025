import os
from Parser import load_model
from SolutionValidator import validate_solution, parse_solution_file


def main(instance_file, solution_file):
    print(f"Instance '{instance_file}'")
    model = load_model(instance_file)

    print("\nModel Summary:")
    print(f"Number of nodes: {model.num_nodes}")
    print(f"Number of families: {model.num_fam}")
    print(f"Required visits: {model.num_req}")
    print(f"Vehicle capacity: {model.capacity}")
    print(f"Number of vehicles: {model.vehicles}")

    print("\nFamily information:")
    for i, family in enumerate(model.families):
        print(
            f"Family {i}: {len(family.nodes)} members, {family.required_visits} required visits, demand: {family.demand}")

    # If a solution file is provided, validate it
    if solution_file:
        if not os.path.exists(solution_file):
            print(f"Error: Solution file '{solution_file}' does not exist.")
            return

        print(f"\nValidating solution from '{solution_file}'...")
        routes = parse_solution_file(solution_file)

        # Print routes summary
        print("\nRoutes:")
        for i, route in enumerate(routes):
            print(f"Route {i}: {route}")

        valid, report = validate_solution(model, routes)

        if valid:
            print("\nSolution is VALID.")
            print(f"Total cost: {report['total_cost']}")
            print("\nRoute details:")
            for i, (load, cost) in enumerate(zip(report['route_loads'], report['route_costs'])):
                print(f"Route {i}: Load = {load}/{model.capacity}, Cost = {cost}")

            print("\nFamily visits:")
            for family_id, visits in report['family_visits'].items():
                family = model.families[family_id]
                print(f"Family {family_id}: {visits}/{family.required_visits} required visits")
        else:
            print("\nSolution is INVALID.")
            print("Errors:")
            for error in report['errors']:
                print(f"- {error}")


if __name__ == "__main__":
    main("fcvrp_P-n101-k4_10_3_3.txt", "solution_example.txt")