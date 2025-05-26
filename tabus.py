# -*- coding: utf-8 -*-
import random
from collections import deque
from const_heuristic import Fcvrp  # Χρειάζεται μια αρχική λύση

def calculate_total_cost(solution, costs):
    """
    Υπολογίζει το συνολικό κόστος μιας διαδρομής.

    Args:
        solution: Μια λίστα που περιέχει τις διαδρομές των οχημάτων, όπου κάθε διαδρομή είναι λίστα κόμβων.
        costs: Ο πίνακας κόστους. Το costs[i,j] είναι το κόστος μετάβασης από τον κόμβο i στον κόμβο j.

    Returns:
        Το συνολικό κόστος της λύσης, δηλαδή το άθροισμα των αποστάσεων για όλες τις διαδρομές.
    """
    total_cost = 0
    for route in solution:
        if route:
            total_cost += costs[0][route[0]]  # Από αποθήκη στον πρώτο κόμβο
            for i in range(len(route) - 1):
                total_cost += costs[route[i]][route[i + 1]]  # Κόστος μεταξύ κόμβων στη διαδρομή
            total_cost += costs[route[-1]][0]  # Από τον τελευταίο κόμβο πίσω στην αποθήκη
    return total_cost


def get_neighbors(solution):
    """
    Δημιουργεί μία λίστα από γειτονικές λύσεις κάνοντας ανταλλαγές κόμβων μεταξύ διαφορετικών routes.

    Args:
        solution: Η τρέχουσα λύση (λίστα με routes).

    Returns:
        neighbors: Λίστα με νέες λύσεις που προκύπτουν από swap μεταξύ κόμβων διαφορετικών routes.
        moves: Λίστα με τις κινήσεις (ανταλλαγές) που έγιναν ώστε να παραχθεί η κάθε νέα λύση.
    """
    neighbors = []
    moves = []

    for i in range(len(solution)):
        for j in range(i + 1, len(solution)):  # Συνδυασμοί routes
            route1 = solution[i]
            route2 = solution[j]
            for idx1 in range(len(route1)):
                for idx2 in range(len(route2)):
                    new_solution = [r[:] for r in solution]  # Αντιγραφή λύσης
                    new_solution[i][idx1], new_solution[j][idx2] = new_solution[j][idx2], new_solution[i][idx1]
                    neighbors.append(new_solution)
                    moves.append(((route1[idx1], route2[idx2]), (i, j)))  # Καταγραφή κίνησης
    return neighbors, moves


def tabu_search(local_solution, costs, tabu_size, max_iterations):
    """
    Εκτελεί τον αλγόριθμο Tabu Search για να βρει βελτιωμένη λύση στο πρόβλημα.

    Args:
        local_solution: Η λύση από τον Local Search.
        costs: Ο πίνακας κόστους του προβλήματος.
        tabu_size: Το μέγεθος της λίστας tabu, δηλαδή πόσες κινήσεις θυμόμαστε ώστε να μην τις επαναλάβουμε.
        max_iterations: Ο μέγιστος αριθμός επαναλήψεων που θα εκτελέσει ο αλγόριθμος.

    Returns:
        best_solution: Η καλύτερη λύση που βρέθηκε κατά την εκτέλεση του αλγορίθμου.
        best_cost: Το κόστος της καλύτερης λύσης.
    """
    current_solution = local_solution
    current_cost = calculate_total_cost(current_solution, costs)

    best_solution = current_solution
    best_cost = current_cost

    tabu_list = deque(maxlen=tabu_size)  # Λίστα απαγορευμένων κινήσεων

    for iteration in range(max_iterations):
        neighbors, moves = get_neighbors(current_solution)

        best_neighbor = None
        best_neighbor_cost = float("inf")
        best_move = None

        for neighbor, move in zip(neighbors, moves):
            move_nodes = tuple(sorted(move[0]))  # Κανονικοποίηση της κίνησης (ανεξαρτήτως σειράς)

            if move_nodes in tabu_list:
                continue  # Αν είναι tabu η κίνηση, την προσπερνάμε

            cost = calculate_total_cost(neighbor, costs)
            if cost < best_neighbor_cost:
                best_neighbor = neighbor
                best_neighbor_cost = cost
                best_move = move_nodes

        # Αν όλες οι κινήσεις ήταν tabu, κάνε μια παρόμοια εναλλακτική (aspiration criterion)
        if not best_neighbor:
            best_neighbor = neighbors[0]
            best_neighbor_cost = calculate_total_cost(best_neighbor, costs)
            best_move = tuple(sorted(moves[0][0]))

        # Ενημέρωση τρέχουσας λύσης και προσθήκη της κίνησης στη tabu λίστα
        current_solution = best_neighbor
        current_cost = best_neighbor_cost
        tabu_list.append(best_move)

        # Αν η νέα λύση είναι καλύτερη από τη συνολικά καλύτερη, την αποθηκεύουμε
        if current_cost < best_cost:
            best_solution = current_solution
            best_cost = current_cost


    return best_solution, best_cost
