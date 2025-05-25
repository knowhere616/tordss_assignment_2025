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

def write_solution_to_file(solution, filename="solution.txt"):
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
            for route in solution:
                if route:  # Έλεγχος αν η διαδρομή δεν είναι άδεια
                    # Προσθήκη του depot (0) στην αρχή και στο τέλος κάθε διαδρομής
                    # και μετατροπή όλων των στοιχείων σε str για το join
                    formatted_route = "0 " + " ".join(map(str, route)) + " 0"
                    f.write(formatted_route + "\n")
        print(f"\nΗ λύση γράφτηκε με επιτυχία στο αρχείο: {filename}")
    except IOError:
        print(f"\nΠαρουσιάστηκε σφάλμα κατά την εγγραφή στο αρχείο: {filename}")

if __name__ == "__main__":
    # Δημιουργία μιας περίπτωσης του προβλήματος και παραγωγή μιας αρχικής λύσης
    # Βεβαιωθείτε ότι το όνομα του αρχείου instance είναι σωστό
    instance_file = "fcvrp_P-n101-k4_10_3_3.txt" # [cite: 14]
    # Ορισμός ενός από τους επιτρεπόμενους σπόρους [cite: 20]
    random_seed = 4 # Μπορείτε να επιλέξετε έναν από τους: 4, 8, 15, 16, 23, 42 [cite: 20]
    random.seed(random_seed)
    print(f"Χρησιμοποιείται ο σπόρος (seed): {random_seed}")

    fcvrp_instance = Fcvrp(instance_file) 
    fcvrp_instance.visit_nodes() # Υποθέτοντας ότι αυτή η μέθοδος παράγει την αρχική λύση
    initial_solution = fcvrp_instance.solution
    costs = fcvrp_instance.costs

    # Έλεγχος αν η initial_solution είναι έγκυρη (όχι None και όχι κενή λίστα)
    if not initial_solution or not any(initial_solution): # Ελέγχει αν είναι κενή ή περιέχει μόνο κενές διαδρομές
        print("Η αρχική λύση είναι κενή ή δεν περιέχει έγκυρες διαδρομές. Η τοπική αναζήτηση δεν μπορεί να εκτελεστεί.")
    else:
        # Εκτύπωση αρχικής λύσης
        print("\n--- Αρχική Λύση ---")
        if all(isinstance(r, list) for r in initial_solution):
            # Φιλτράρισμα κενών διαδρομών από την εκτύπωση, αν υπάρχουν
            printable_initial_solution = [route for route in initial_solution if route]
            print("Λύση:", printable_initial_solution)
            print("Κόστος:", calculate_total_cost(initial_solution, costs))
        else:
            print("Λύση: Μη έγκυρη μορφή αρχικής λύσης για εκτύπωση.")
            # Για να αποφύγουμε σφάλμα παρακάτω, αν η μορφή είναι τελείως λάθος
            # μπορεί να χρειαστεί να τερματίσουμε ή να θέσουμε μια default κενή λύση.
            # Ωστόσο, η const_heuristic.py θα πρέπει να επιστρέφει λίστα από λίστες.


        # Εκτέλεση της τοπικής αναζήτησης
        best_solution, best_cost = local_search(initial_solution, costs, max_iterations=100)

        # Εκτύπωση αποτελεσμάτων
        print("\n--- Βελτιωμένη Λύση (Τοπική Αναζήτηση) ---")
        if all(isinstance(r, list) for r in best_solution):
             # Φιλτράρισμα κενών διαδρομών από την εκτύπωση, αν υπάρχουν
            printable_best_solution = [route for route in best_solution if route]
            print("Βέλτιστη Λύση:", printable_best_solution)
        else:
            print("Βέλτιστη Λύση: Μη έγκυρη μορφή βέλτιστης λύσης για εκτύπωση.")
        print("Βέλτιστο Κόστος:", best_cost)

        # Εγγραφή της βέλτιστης λύσης στο αρχείο
        # Ο κώδικας σας πρέπει να παράγει ένα txt αρχείο με την τελική σας λύση, το οποίο να
        # ακολουθεί το format του αρχείου solution_example.txt. [cite: 17]
        # Το αρχείο αυτό πρέπει να βρίσκεται ήδη στο folder με το python project σας. [cite: 18]
        write_solution_to_file(best_solution, "solution.txt")