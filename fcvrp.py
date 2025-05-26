# -*- coding: utf-8 -*-
import random
from const_heuristic import Fcvrp
from tabus import tabu_search

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
        if not neighbors: # Αν δεν υπάρχουν γείτονες (π.χ. όλες οι διαδρομές έχουν < 2 πελάτες)
            break
            
        current_best_neighbor = None
        current_best_neighbor_cost = best_cost

        for neighbor in neighbors:
            neighbor_cost = calculate_total_cost(neighbor, costs)
            if neighbor_cost < current_best_neighbor_cost:
                current_best_neighbor_cost = neighbor_cost
                current_best_neighbor = neighbor
        
        if current_best_neighbor and current_best_neighbor_cost < best_cost:
            best_cost = current_best_neighbor_cost
            best_solution = [list(r) for r in current_best_neighbor] # Αποθήκευση αντιγράφου
            current_solution = current_best_neighbor # Μετάβαση στην καλύτερη γειτονική λύση αυτής της επανάληψης
        else:
            break  # Τερματισμός αν δεν βρεθεί καλύτερη γειτονική λύση στην τρέχουσα επανάληψη

    return best_solution, best_cost

def format_solution(solution):
    # Μετατρέπει μια λύση από τη μορφή λίστας διαδρομών σε μία ενιαία συμβολοσειρά.
    all_nodes = []
    for route in solution:
        if route:
            all_nodes.extend(route)
    return "0 " + " ".join(map(str, all_nodes)) + " 0"

def write_solution_to_file(initial_solution, local_solution, tabu_solution, filename="solution.txt"):
    """
    Γράφει τη λύση σε ένα αρχείο txt με την καθορισμένη μορφή.
    Κάθε διαδρομή ξεκινά και τελειώνει με τον κόμβο 0 (αποθήκη).

    Args:
        solution: Μια λίστα με τις διαδρομές των οχημάτων.
                  Κάθε διαδρομή είναι μια λίστα με τους κόμβους που επισκέπτεται το όχημα,
                  μη συμπεριλαμβάνοντας την αρχική και τελική αποθήκη.
        filename: Το όνομα του αρχείου εξόδου.
    """
    try:
        with open(filename, 'w') as f:
            # Γράφουμε την Αρχική Λύση
            f.write(format_solution(initial_solution) + "\n")
            
            # Γράφουμε τη λύση της Τοπικής Αναζήτησης
            f.write(format_solution(local_solution) + "\n")
            
            # Γράφουμε τη λύση της Τabu Αναζήτησης
            if tabu_solution:
                f.write(format_solution(tabu_solution) + "\n")
                
        print(f"\nΟι λύσεις γράφτηκαν με επιτυχία στο αρχείο: {filename}")
    except IOError:
        print(f"\nΠαρουσιάστηκε σφάλμα κατά την εγγραφή στο αρχείο: {filename}")

if __name__ == "__main__":
    # Φόρτωση δεδομένων
    instance_file = "fcvrp_P-n101-k4_10_3_3.txt"
    random_seed = 4 # [seeds: 4, 8, 15, 16, 23, 42]
    random.seed(random_seed)
    print(f"Χρησιμοποιείται ο σπόρος (seed): {random_seed}")

    # 1. Δημιουργία αρχικής λύσης
    fcvrp_instance = Fcvrp(instance_file) 
    fcvrp_instance.visit_nodes() # Υποθέτοντας ότι αυτή η μέθοδος παράγει την αρχική λύση
    initial_solution = fcvrp_instance.solution
    costs = fcvrp_instance.costs

    if not initial_solution or not any(initial_solution): # Ελέγχει αν είναι κενή ή περιέχει μόνο κενές διαδρομές
        print("Η αρχική λύση είναι κενή ή δεν περιέχει έγκυρες διαδρομές. Η τοπική αναζήτηση δεν μπορεί να εκτελεστεί.")
    else:
        print("\n--- Αρχική Λύση (Κατασκευαστικός Αλγόριθμος) ---")
        if all(isinstance(r, list) for r in initial_solution):
            # Φιλτράρισμα κενών διαδρομών από την εκτύπωση, αν υπάρχουν
            printable_initial_solution = [route for route in initial_solution if route]
            print("Λύση:", printable_initial_solution)
            print("Κόστος Αρχικής Λύσης:", calculate_total_cost(initial_solution, costs))
        else:
            print("Λύση: Μη έγκυρη μορφή αρχικής λύσης για εκτύπωση.")


        # 2. Εκτέλεση Απλού Τοπικού Αλγορίθμου Αναζήτησης
        local_solution, local_cost = local_search(initial_solution, costs, max_iterations=100)
        print("\n--- Βελτιωμένη Λύση (Απλός Τοπικός Αλγόριθμος) ---")
        if all(isinstance(r, list) for r in local_solution):
             # Φιλτράρισμα κενών διαδρομών από την εκτύπωση, αν υπάρχουν
            printable_local_solution = [route for route in local_solution if route]
            print("Βέλτιστη Λύση:", printable_local_solution)
        else:
            print("Βέλτιστη Λύση: Μη έγκυρη μορφή βέλτιστης λύσης για εκτύπωση.")
        print("Κόστος Λύσης Τοπικού Αλγορίθμου:", local_cost)

        # 3. Εκτέλεση Tabu Search (ξεκινώντας από την αρχική λύση)
        tabu_solution, tabu_cost = tabu_search(local_solution, costs, tabu_size=50, max_iterations=600) # Πολλές επαναλήψεις [tabu size] για καλύτερη εξερεύνηση
        print("\n--- Βελτιωμένη Λύση (Tabu Search) ---")
        printable_tabu_solution = [route for route in tabu_solution if route]
        print("Λύση:", printable_tabu_solution)
        print("Κόστος Λύσης Tabu Search:", tabu_cost)

        # 5. Εγγραφή της καλύτερης λύσης στο αρχείο
        write_solution_to_file(initial_solution, local_solution, tabu_solution)