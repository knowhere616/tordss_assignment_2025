# -*- coding: utf-8 -*-
import random
from const_heuristic import Fcvrp  # Βεβαιώσου ότι έχεις το Fcvrp class

def calculate_total_cost(solution, costs):
    """
    Υπολογίζει το συνολικό κόστος μιας λύσης.

    Args:
        solution: Μια λίστα με τις διαδρομές των οχημάτων, όπου κάθε διαδρομή είναι μια λίστα με τους κόμβους που επισκέπτεται το όχημα.
        costs: Ένας πίνακας κόστους όπου costs[i][j] είναι το κόστος μετάβασης από τον κόμβο i στον κόμβο j.

    Returns:
        Το συνολικό κόστος της λύσης.
    """
    total_cost = 0
    for route in solution:
        if route:  # Έλεγχος αν η διαδρομή δεν είναι άδεια
            total_cost += costs[0][route[0]]  # Κόστος από την αποθήκη στον πρώτο κόμβο
            for i in range(len(route) - 1):
                total_cost += costs[route[i]][route[i+1]]  # Κόστος μεταξύ των κόμβων της διαδρομής
            total_cost += costs[route[-1]][0]  # Κόστος από τον τελευταίο κόμβο στην αποθήκη
    return total_cost

def get_neighbors(solution):
    """
    Δημιουργεί μια λίστα με γειτονικές λύσεις κάνοντας μικρές αλλαγές στην τρέχουσα λύση.
    Εδώ χρησιμοποιούμε την αλλαγή θέσης δύο κόμβων σε μια διαδρομή ως κίνηση γειτονιάς.

    Args:
        solution: Η τρέχουσα λύση.

    Returns:
        Μια λίστα με τις γειτονικές λύσεις.
    """
    neighbors = []
    for route_index, route in enumerate(solution):
        if len(route) > 1:
            for i in range(len(route)):
                for j in range(i + 1, len(route)):
                    neighbor = [list(r) for r in solution]  # Δημιουργία αντιγράφου της λύσης
                    neighbor[route_index][i], neighbor[route_index][j] = neighbor[route_index][j], neighbor[route_index][i]  # Αλλαγή θέσης δύο κόμβων
                    neighbors.append(neighbor)
    return neighbors

def local_search(initial_solution, costs, max_iterations=100):
    """
    Εκτελεί την αλγόριθμο τοπικής αναζήτησης για τη βελτιστοποίηση της αρχικής λύσης.

    Args:
        initial_solution: Η αρχική λύση που παρήχθη από το heuristic.
        costs: Ο πίνακας κόστους μεταξύ των κόμβων.
        max_iterations: Ο μέγιστος αριθμός επαναλήψεων της τοπικής αναζήτησης.

    Returns:
        Η καλύτερη λύση που βρέθηκε και το κόστος της.
    """
    current_solution = initial_solution
    best_solution = initial_solution
    best_cost = calculate_total_cost(initial_solution, costs)

    for _ in range(max_iterations):
        neighbors = get_neighbors(current_solution)
        for neighbor in neighbors:
            neighbor_cost = calculate_total_cost(neighbor, costs)
            if neighbor_cost < best_cost:
                best_cost = neighbor_cost
                best_solution = [list(r) for r in neighbor]  # Αποθήκευση αντιγράφου
                current_solution = neighbor
                break  # Μετάβαση στην καλύτερη γειτονική λύση
        else:
            break  # Τερματισμός αν δεν βρεθεί καλύτερη γειτονική λύση

    return best_solution, best_cost

if __name__ == "__main__":
    # Δημιουργία μιας περίπτωσης του προβλήματος και παραγωγή μιας αρχικής λύσης
    fcvrp_instance = Fcvrp("fcvrp_P-n101-k4_10_3_3.txt")
    fcvrp_instance.visit_nodes()
    initial_solution = fcvrp_instance.solution
    costs = fcvrp_instance.costs

    # Εκτέλεση της τοπικής αναζήτησης
    best_solution, best_cost = local_search(initial_solution, costs, max_iterations=100)

    # Εκτύπωση αποτελεσμάτων
    print("\n--- Αρχική Λύση ---")
    print("Λύση:", initial_solution)
    print("Κόστος:", calculate_total_cost(initial_solution, costs))

    print("\n--- Βελτιωμένη Λύση (Τοπική Αναζήτηση) ---")
    print("Βέλτιστη Λύση:", best_solution)
    print("Βέλτιστο Κόστος:", best_cost)