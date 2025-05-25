# -*- coding: utf-8 -*-
import random
from collections import deque
from const_heuristic import Fcvrp  # Βεβαιώσου ότι έχεις το Fcvrp class

# --- Βασικές Συναρτήσεις (Κοινές ή από το αρχικό fcvrp.py) ---

def calculate_total_cost(solution, costs):
    """
    Υπολογίζει το συνολικό κόστος μιας λύσης.
    """
    total_cost = 0
    for route in solution:
        if route:  # Έλεγχος αν η διαδρομή δεν είναι άδεια
            total_cost += costs[0][route[0]]  # Κόστος από την αποθήκη στον πρώτο κόμβο
            for i in range(len(route) - 1):
                total_cost += costs[route[i]][route[i+1]]  # Κόστος μεταξύ των κόμβων της διαδρομής
            total_cost += costs[route[-1]][0]  # Κόστος από τον τελευταίο κόμβο στην αποθήκη
    return total_cost

def write_solution_to_file(solution, filename="solution.txt"):
    """
    Γράφει τη λύση σε ένα αρχείο txt με την καθορισμένη μορφή.
    Κάθε διαδρομή ξεκινά και τελειώνει με τον κόμβο 0 (αποθήκη).
    """
    try:
        with open(filename, 'w') as f:
            for route in solution:
                if route:  # Έλεγχος αν η διαδρομή δεν είναι άδεια
                    formatted_route = "0 " + " ".join(map(str, route)) + " 0"
                    f.write(formatted_route + "\n")
        print(f"\nΗ βέλτιστη λύση γράφτηκε με επιτυχία στο αρχείο: {filename}")
    except IOError:
        print(f"\nΠαρουσιάστηκε σφάλμα κατά την εγγραφή στο αρχείο: {filename}")

# --- Συναρτήσεις για τον Απλό Τοπικό Αλγόριθμο Αναζήτησης ---

def get_local_search_neighbors(solution):
    """
    Δημιουργεί γειτονικές λύσεις για τον απλό τοπικό αλγόριθμο αναζήτησης (intra-route swap).
    """
    neighbors = []
    for route_index, route in enumerate(solution):
        if len(route) > 1:
            for i in range(len(route)):
                for j in range(i + 1, len(route)):
                    neighbor = [list(r) for r in solution]
                    neighbor[route_index][i], neighbor[route_index][j] = neighbor[route_index][j], neighbor[route_index][i]
                    neighbors.append(neighbor)
    return neighbors

def local_search(initial_solution, costs, max_iterations=100):
    """
    Εκτελεί τον απλό αλγόριθμο τοπικής αναζήτησης (best improvement, intra-route swap).
    """
    current_solution = [list(r) for r in initial_solution]
    best_solution_ls = [list(r) for r in initial_solution] # Καλύτερη λύση που βρέθηκε από το local search
    best_cost_ls = calculate_total_cost(best_solution_ls, costs)

    for iteration in range(max_iterations):
        neighbors = get_local_search_neighbors(current_solution)
        if not neighbors:
            break # Δεν υπάρχουν γείτονες για βελτίωση

        found_better_neighbor_in_iteration = False
        current_iteration_best_solution = current_solution
        current_iteration_best_cost = calculate_total_cost(current_solution, costs)

        for neighbor in neighbors:
            neighbor_cost = calculate_total_cost(neighbor, costs)
            if neighbor_cost < current_iteration_best_cost:
                current_iteration_best_cost = neighbor_cost
                current_iteration_best_solution = [list(r) for r in neighbor]
                found_better_neighbor_in_iteration = True
        
        if found_better_neighbor_in_iteration:
            current_solution = current_iteration_best_solution
            if current_iteration_best_cost < best_cost_ls:
                best_cost_ls = current_iteration_best_cost
                best_solution_ls = current_iteration_best_solution
        else:
            break # Δεν βρέθηκε καλύτερος γείτονας σε αυτή την επανάληψη, τοπικό βέλτιστο

    return best_solution_ls, best_cost_ls

# --- Συναρτήσεις για τον Αλγόριθμο Tabu Search ---

def get_tabu_neighbors_and_moves(solution):
    """
    Δημιουργεί γειτονικές λύσεις για τον Tabu Search (inter-route swap) και τις κινήσεις που τις παρήγαγαν.
    """
    neighbors = []
    moves = [] # ( (node1, node2), (route_idx1, route_idx2) )

    # Φιλτράρισμα μη-κενών διαδρομών για ανταλλαγές
    non_empty_routes_indices = [idx for idx, r in enumerate(solution) if r]
    
    for i_idx in range(len(non_empty_routes_indices)):
        for j_idx in range(i_idx + 1, len(non_empty_routes_indices)):
            route1_orig_idx = non_empty_routes_indices[i_idx]
            route2_orig_idx = non_empty_routes_indices[j_idx]

            route1 = solution[route1_orig_idx]
            route2 = solution[route2_orig_idx]

            for node_idx1 in range(len(route1)):
                for node_idx2 in range(len(route2)):
                    new_solution = [list(r) for r in solution]
                    
                    # Εκτέλεση της ανταλλαγής
                    val1 = new_solution[route1_orig_idx][node_idx1]
                    val2 = new_solution[route2_orig_idx][node_idx2]
                    new_solution[route1_orig_idx][node_idx1] = val2
                    new_solution[route2_orig_idx][node_idx2] = val1
                    
                    neighbors.append(new_solution)
                    # Αποθήκευση της κίνησης: οι κόμβοι που ανταλλάχθηκαν και οι αρχικοί τους δείκτες διαδρομών
                    # Η κίνηση ορίζεται από τους δύο κόμβους που ανταλλάσσονται
                    swapped_nodes = tuple(sorted((route1[node_idx1], route2[node_idx2])))
                    moves.append(swapped_nodes)
    return neighbors, moves


def tabu_search(initial_solution, costs, tabu_size=10, max_iterations=200):
    """
    Εκτελεί τον αλγόριθμο Tabu Search.
    """
    current_solution = [list(r) for r in initial_solution]
    current_cost = calculate_total_cost(current_solution, costs)

    best_solution_overall = [list(r) for r in current_solution] # Καλύτερη λύση που βρέθηκε ποτέ
    best_cost_overall = current_cost

    tabu_list = deque(maxlen=tabu_size)

    for iteration in range(max_iterations):
        # neighbors_with_moves = [(neighbor, move), ...]
        candidate_neighbors, candidate_moves = get_tabu_neighbors_and_moves(current_solution)
        
        best_neighbor_this_iteration = None
        best_neighbor_cost_this_iteration = float("inf")
        best_move_this_iteration = None

        # Εύρεση του καλύτερου μη-tabu γείτονα
        for neighbor, move in zip(candidate_neighbors, candidate_moves):
            # Η 'move' είναι ήδη ένα tuple των ανταλλασσόμενων κόμβων, π.χ. (node_A, node_B)
            # Το move αποθηκεύεται στη tabu list ως tuple ταξινομημένων κόμβων
            # current_move_tuple = tuple(sorted(move)) # Η move είναι ήδη ταξινομημένη από το get_tabu_neighbors_and_moves

            if move in tabu_list: # Αν η κίνηση είναι tabu
                # Aspiration Criterion: Αν παρόλα αυτά οδηγεί σε λύση καλύτερη από την best_overall
                cost_if_aspirated = calculate_total_cost(neighbor, costs)
                if cost_if_aspirated < best_cost_overall:
                    # Επιτρέπουμε την tabu κίνηση (Aspiration)
                    pass # Συνεχίζουμε για να την αξιολογήσουμε κανονικά
                else:
                    continue # Αλλιώς, αγνοούμε την tabu κίνηση
            
            cost = calculate_total_cost(neighbor, costs)
            if cost < best_neighbor_cost_this_iteration:
                best_neighbor_this_iteration = neighbor
                best_neighbor_cost_this_iteration = cost
                best_move_this_iteration = move # Αυτή είναι η κίνηση που θα γίνει tabu

        if best_neighbor_this_iteration is None and candidate_neighbors: # Αν όλοι οι γείτονες ήταν tabu (και δεν πληρούσαν κριτήριο aspiration) ή δεν βρέθηκε κανένας
             # Αυτό το κομμάτι είναι από τον αρχικό σας κώδικα tabus.py
             # Επιλέγουμε τον πρώτο γείτονα αν δεν βρέθηκε άλλος (π.χ. όλοι tabu και όχι καλύτεροι από best_overall)
             # Ωστόσο, αυτό θα μπορούσε να επιλέξει μια tabu κίνηση χωρίς aspiration.
             # Μια πιο ασφαλής προσέγγιση θα ήταν να σταματήσει αν δεν υπάρχουν έγκυρες κινήσεις.
             # Για τώρα, διατηρώ την αρχική λογική σας:
            idx_to_pick = 0
            if not candidate_moves: # Αν δεν υπήρχαν καθόλου κινήσεις/γείτονες
                 print(f"Tabu Search: Δεν βρέθηκαν γείτονες στην επανάληψη {iteration + 1}. Διακοπή.")
                 break
            best_neighbor_this_iteration = candidate_neighbors[idx_to_pick]
            best_neighbor_cost_this_iteration = calculate_total_cost(best_neighbor_this_iteration, costs)
            best_move_this_iteration = candidate_moves[idx_to_pick] # tuple(sorted(candidate_moves[idx_to_pick]))
            # print(f"Warning: Tabu search picked potentially a tabu move or first available move in iteration {iteration+1}")


        if best_neighbor_this_iteration:
            current_solution = [list(r) for r in best_neighbor_this_iteration]
            current_cost = best_neighbor_cost_this_iteration
            
            if best_move_this_iteration: # Προσθήκη της κίνησης στη λίστα tabu
                 tabu_list.append(best_move_this_iteration)

            if current_cost < best_cost_overall: # Αν η νέα λύση είναι καλύτερη από την συνολικά καλύτερη
                best_solution_overall = [list(r) for r in current_solution]
                best_cost_overall = current_cost
        else:
            # Δεν βρέθηκε κανένας γείτονας (π.χ. η get_tabu_neighbors_and_moves επέστρεψε κενές λίστες)
            print(f"Tabu Search: Δεν βρέθηκε κατάλληλος γείτονας στην επανάληψη {iteration + 1}. Διακοπή.")
            break
        
        # print(f"Iteration {iteration + 1}: Current Cost = {current_cost}, Best Overall Cost = {best_cost_overall}")


    return best_solution_overall, best_cost_overall


# --- Κύριο Μέρος του Script ---
if __name__ == "__main__":
    instance_file = "fcvrp_P-n101-k4_10_3_3.txt"
    # Ορισμός ενός από τους επιτρεπόμενους σπόρους [cite: 20]
    random_seed = 42 # Μπορείτε να επιλέξετε: 4, 8, 15, 16, 23, 42
    random.seed(random_seed)
    print(f"Χρησιμοποιείται ο σπόρος (seed): {random_seed}")

    # 1. Δημιουργία αρχικής λύσης
    fcvrp_instance = Fcvrp(instance_file)
    fcvrp_instance.visit_nodes() # Αυτή η μέθοδος πρέπει να επιστρέφει μια έγκυρη αρχική λύση
    initial_solution = fcvrp_instance.solution
    costs = fcvrp_instance.costs # Ο πίνακας κόστους

    if not initial_solution or not any(r for r in initial_solution):
        print("Η αρχική λύση είναι κενή ή δεν περιέχει έγκυρες διαδρομές. Τερματισμός.")
        exit()

    initial_cost = calculate_total_cost(initial_solution, costs)
    print("\n--- Αρχική Λύση (Κατασκευαστικός Αλγόριθμος) ---")
    # Φιλτράρισμα κενών διαδρομών από την εκτύπωση
    printable_initial_solution = [route for route in initial_solution if route]
    print("Λύση:", printable_initial_solution)
    print("Κόστος Αρχικής Λύσης:", initial_cost)

    # 2. Εκτέλεση Απλού Τοπικού Αλγορίθμου Αναζήτησης
    ls_solution, ls_cost = local_search(initial_solution, costs, max_iterations=100)
    print("\n--- Βελτιωμένη Λύση (Απλός Τοπικός Αλγόριθμος) ---")
    printable_ls_solution = [route for route in ls_solution if route]
    print("Λύση:", printable_ls_solution)
    print("Κόστος Λύσης Τοπικού Αλγορίθμου:", ls_cost)

    # 3. Εκτέλεση Tabu Search (ξεκινώντας από την αρχική λύση)
    # Μπορείτε εναλλακτικά να ξεκινήσετε το Tabu Search από τη λύση του Local Search:
    # tabu_solution, tabu_cost = tabu_search(ls_solution, costs, tabu_size=15, max_iterations=300)
    tabu_solution, tabu_cost = tabu_search(initial_solution, costs, tabu_size=15, max_iterations=300) # Αυξάνω λίγο τις επαναλήψεις/tabu size για καλύτερη εξερεύνηση
    print("\n--- Βελτιωμένη Λύση (Tabu Search) ---")
    printable_tabu_solution = [route for route in tabu_solution if route]
    print("Λύση:", printable_tabu_solution)
    print("Κόστος Λύσης Tabu Search:", tabu_cost)

    # 4. Επιλογή της καλύτερης λύσης για εγγραφή στο αρχείο
    final_best_solution = initial_solution
    final_best_cost = initial_cost

    if ls_cost < final_best_cost:
        final_best_solution = ls_solution
        final_best_cost = ls_cost
    
    if tabu_cost < final_best_cost:
        final_best_solution = tabu_solution
        final_best_cost = tabu_cost
    
    print("\n--- Συνολικά Καλύτερη Λύση ---")
    printable_final_best_solution = [route for route in final_best_solution if route]
    print("Λύση:", printable_final_best_solution)
    print("Κόστος:", final_best_cost)

    # 5. Εγγραφή της καλύτερης λύσης στο αρχείο
    # Ο κώδικας σας πρέπει να παράγει ένα txt αρχείο με την τελική σας λύση,
    # το οποίο να ακολουθεί το format του αρχείου solution_example.txt. [cite: 17]
    # Το αρχείο αυτό πρέπει να βρίσκεται ήδη στο folder με το python project σας. [cite: 18]
    write_solution_to_file(final_best_solution, "solution.txt")