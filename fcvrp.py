# -*- coding: utf-8 -*-
from Parser import *
import math
import random
import copy # Για deep copies λύσεων

class Fcvrp:
    # --- Αρχικές παράμετροι και φόρτωση δεδομένων ---
    def __init__(self, filename, seed=42): # Προσθήκη seed
        self.filename = filename
        self.model = None
        self.costs = [] # Πίνακας κόστους (αποστάσεων)
        self.node_demands = {} # Λεξικό: node_id -> demand
        self.node_families = {} # Λεξικό: node_id -> family_id
        self.family_nodes = {}  # Λεξικό: family_id -> list of node_ids in family
        self.required_visits_per_family = {} # Λεξικό: family_id -> vl (απαιτούμενες επισκέψεις)
        self.TRUCK_CAPACITY = 0
        self.MAX_TRUCKS = 0
        self.N_FAMILIES = 0 # Αριθμός οικογενειών
        self.N_CUSTOMERS = 0 # Αριθμός πελατών (κόμβων εκτός αποθήκης)
        self.DEPOT_NODE = 0 # Ο κόμβος της αποθήκης είναι πάντα ο 0

        self.solution = [] # Η τελική λύση (λίστα δρομολογίων)
        self.total_cost = float('inf') # Το συνολικό κόστος της λύσης

        random.seed(seed) # Αρχικοποίηση γεννήτριας τυχαίων αριθμών

        self._load_data() # Καλεί τις εσωτερικές μεθόδους φόρτωσης

    def _load_data(self):
        """Φορτώνει όλα τα απαραίτητα δεδομένα από το αρχείο."""
        print(f"--- Loading data from {self.filename} ---")
        self.model = load_model(self.filename)

        # Έλεγχος αν το μοντέλο φορτώθηκε σωστά
        if not self.model:
            raise ValueError("Failed to load model from parser.")

        # Αποθήκευση βασικών παραμέτρων
        self.TRUCK_CAPACITY = self.model.capacity
        self.MAX_TRUCKS = self.model.max_vehicles # Χρησιμοποιούμε το όνομα από το parser
        self.N_FAMILIES = len(self.model.families)
        self.N_CUSTOMERS = self.model.n_customers # Χρησιμοποιούμε το όνομα από το parser

        print(f"Instance Parameters:")
        print(f"  Customers: {self.N_CUSTOMERS}")
        print(f"  Families: {self.N_FAMILIES}")
        print(f"  Truck Capacity (Q): {self.TRUCK_CAPACITY}")
        print(f"  Max Trucks (K): {self.MAX_TRUCKS}")


        # Φόρτωση κόστους (πίνακας αποστάσεων)
        # Υποθέτουμε ότι το self.model.costs είναι ο σωστός πίνακας [depot+customers]x[depot+customers]
        if hasattr(self.model, 'costs') and self.model.costs:
             self.costs = self.model.costs
             # Επιβεβαίωση διαστάσεων (π.χ. (101 x 101) για P-n101-k4...)
             print(f"  Cost matrix loaded with dimensions: {len(self.costs)}x{len(self.costs[0]) if self.costs else 0}")
             if len(self.costs) != self.N_CUSTOMERS + 1:
                 print(f"  Warning: Cost matrix rows ({len(self.costs)}) mismatch expected ({self.N_CUSTOMERS + 1})")
        else:
             # Χειροκίνητη φόρτωση αν δεν υπάρχει στο model (όπως στον αρχικό κώδικα)
             print("  Loading costs manually...")
             try:
                 with open(self.filename, "r", encoding="utf-8") as file:
                     lines = file.readlines()
                 # Οι γραμμές δεδομένων κόστους ξεκινούν μετά τις γραμμές κεφαλίδας
                 # Προσαρμόστε το εύρος αν η δομή του αρχείου διαφέρει
                 data_lines = lines[4 : 4 + self.N_CUSTOMERS + 1] # +1 για το depot
                 self.costs = []
                 for line in data_lines:
                     row = list(map(int, line.strip().split()))
                     self.costs.append(row)
                 print(f"  Cost matrix loaded manually with dimensions: {len(self.costs)}x{len(self.costs[0]) if self.costs else 0}")
                 if len(self.costs) != self.N_CUSTOMERS + 1:
                      print(f"  Warning: Cost matrix rows ({len(self.costs)}) mismatch expected ({self.N_CUSTOMERS + 1})")
             except Exception as e:
                 raise IOError(f"Error reading cost matrix from file: {e}")


        # Δημιουργία χαρτογραφήσεων κόμβων και απαιτήσεων
        self.family_nodes = {f.id: [n.id for n in f.nodes] for f in self.model.families}

        # Αποθήκευση ζητήσεων και οικογένειας για κάθε κόμβο πελάτη
        # Και απαιτούμενων επισκέψεων ανά οικογένεια (vl)
        print("  Mapping nodes to demands, families, and required visits:")
        for family_id, nodes_in_family in self.family_nodes.items():
            family_obj = next((f for f in self.model.families if f.id == family_id), None)
            if family_obj:
                demand = family_obj.demand # Η ζήτηση είναι ίδια για όλους στην οικογένεια
                req_visits = family_obj.req_customers # Απαιτούμενοι κόμβοι από αυτή την οικογένεια
                self.required_visits_per_family[family_id] = req_visits
                print(f"    Family {family_id}: Requires {req_visits} visits, Node Demand: {demand}")
                for node_id in nodes_in_family:
                    self.node_demands[node_id] = demand
                    self.node_families[node_id] = family_id
            else:
                 print(f"    Warning: Could not find family object for ID {family_id}")


        # Έλεγχος: Συνολικός αριθμός απαιτούμενων πελατών
        total_required = sum(self.required_visits_per_family.values())
        print(f"  Total required customer visits across all families: {total_required}")
        if hasattr(self.model, 'total_req_customers'):
             print(f"  (Matches model.total_req_customers: {self.model.total_req_customers})")


        print("--- Data loading complete ---")


    # --- Βοηθητικές Συναρτήσεις ---
    def get_node_demand(self, node_id):
        """Επιστρέφει τη ζήτηση ενός κόμβου πελάτη."""
        if node_id == self.DEPOT_NODE:
            return 0
        return self.node_demands.get(node_id, 0) # Επιστρέφει 0 αν ο κόμβος δεν βρεθεί

    def get_node_family(self, node_id):
        """Επιστρέφει το ID της οικογένειας ενός κόμβου πελάτη."""
        if node_id == self.DEPOT_NODE:
            return None
        return self.node_families.get(node_id, None)

    def calculate_route_cost(self, route):
        """Υπολογίζει το κόστος ενός δρομολογίου (λίστας κόμβων)."""
        if not route:
            return 0
        cost = 0
        # Κόστος από depot στον πρώτο κόμβο
        cost += self.costs[self.DEPOT_NODE][route[0]]
        # Κόστος μεταξύ διαδοχικών κόμβων
        for i in range(len(route) - 1):
            cost += self.costs[route[i]][route[i+1]]
        # Κόστος από τον τελευταίο κόμβο πίσω στο depot
        cost += self.costs[route[-1]][self.DEPOT_NODE]
        return cost

    def calculate_total_cost(self, solution):
        """Υπολογίζει το συνολικό κόστος μιας λύσης (λίστας δρομολογίων)."""
        total_cost = 0
        for route in solution:
            total_cost += self.calculate_route_cost(route)
        return total_cost

    def calculate_route_load(self, route):
        """Υπολογίζει το συνολικό φορτίο (ζήτηση) ενός δρομολογίου."""
        return sum(self.get_node_demand(node_id) for node_id in route)

    def check_solution_feasibility(self, solution):
        """Ελέγχει αν μια λύση είναι εφικτή (χωρητικότητα, απαιτήσεις vl)."""
        visited_counts_per_family = {fam_id: 0 for fam_id in self.family_nodes}
        all_visited_nodes = set()

        for i, route in enumerate(solution):
            # Έλεγχος χωρητικότητας
            route_load = self.calculate_route_load(route)
            if route_load > self.TRUCK_CAPACITY:
                print(f"Feasibility Check FAILED: Route {i} exceeds capacity ({route_load} > {self.TRUCK_CAPACITY})")
                return False

            # Καταμέτρηση επισκέψεων ανά οικογένεια και διπλότυπων
            for node_id in route:
                if node_id == self.DEPOT_NODE: continue # Αγνοούμε το depot
                if node_id in all_visited_nodes:
                     print(f"Feasibility Check FAILED: Node {node_id} visited more than once.")
                     return False
                all_visited_nodes.add(node_id)
                family_id = self.get_node_family(node_id)
                if family_id is not None:
                    visited_counts_per_family[family_id] += 1
                else:
                     print(f"Feasibility Check WARNING: Node {node_id} in route {i} has no associated family.")


        # Έλεγχος απαιτήσεων vl
        for family_id, required in self.required_visits_per_family.items():
            if visited_counts_per_family[family_id] != required:
                print(f"Feasibility Check FAILED: Family {family_id} requires {required} visits, but solution has {visited_counts_per_family[family_id]}.")
                return False

        # Έλεγχος αριθμού φορτηγών
        if len(solution) > self.MAX_TRUCKS:
             print(f"Feasibility Check FAILED: Solution uses {len(solution)} trucks, but max is {self.MAX_TRUCKS}.")
             return False

        # Αν περάσουν όλοι οι έλεγχοι
        # print("Feasibility Check PASSED.")
        return True


    # --- Αρχικός Κατασκευαστικός Αλγόριθμος (Τροποποιημένος) ---
    def construct_initial_solution(self):
        """Δημιουργεί μια αρχική εφικτή λύση (παρόμοια λογική με πριν, αλλά πιο ευέλικτη)."""
        print("\n--- Constructing Initial Solution ---")
        solution = []
        assigned_nodes = set()
        nodes_per_family_to_visit = copy.deepcopy(self.required_visits_per_family)
        available_nodes_per_family = copy.deepcopy(self.family_nodes) # Κόμβοι που *μπορούν* να επιλεγούν

        truck_id = 0
        while sum(nodes_per_family_to_visit.values()) > 0 and truck_id < self.MAX_TRUCKS:
            current_route = []
            current_load = 0
            print(f"\nStarting Truck {truck_id}...")

            # Προσπάθησε να γεμίσεις το φορτηγό
            can_add_more = True
            while can_add_more:
                best_candidate = None # (node_id, family_id, cost_increase)
                can_add_more = False # Υποθέτουμε ότι δεν μπορούμε να προσθέσουμε άλλο κόμβο

                # Βρες τον καλύτερο υποψήφιο κόμβο για προσθήκη (απλή λογική: κοντινότερος;)
                # (Αυτή η λογική μπορεί να γίνει πολύ πιο έξυπνη, π.χ. cheapest insertion)
                last_node_in_route = current_route[-1] if current_route else self.DEPOT_NODE

                potential_candidates = []
                for family_id, count in nodes_per_family_to_visit.items():
                    if count > 0: # Αν χρειαζόμαστε ακόμα κόμβους από αυτή την οικογένεια
                        for node_id in available_nodes_per_family[family_id]:
                             if node_id not in assigned_nodes:
                                demand = self.get_node_demand(node_id)
                                if current_load + demand <= self.TRUCK_CAPACITY:
                                    cost_increase = self.costs[last_node_in_route][node_id]
                                    potential_candidates.append((node_id, family_id, cost_increase, demand))

                # Επιλογή του "καλύτερου" (εδώ: κοντινότερου) υποψήφιου που χωράει
                if potential_candidates:
                     potential_candidates.sort(key=lambda x: x[2]) # Ταξινόμηση με βάση το κόστος αύξησης
                     best_node_id, best_family_id, _, best_demand = potential_candidates[0]

                     # Προσθήκη του κόμβου
                     current_route.append(best_node_id)
                     current_load += best_demand
                     assigned_nodes.add(best_node_id)
                     nodes_per_family_to_visit[best_family_id] -= 1
                     # Σημαντικό: Αφαίρεσε τον κόμβο από τους διαθέσιμους για *αυτή* την οικογένεια
                     # (Αν και δεν θα ξαναχρησιμοποιηθεί αφού είναι στο assigned_nodes)

                     print(f"  ✅ Added Node {best_node_id} (Family {best_family_id}, Demand {best_demand}) to Truck {truck_id}. Load: {current_load}/{self.TRUCK_CAPACITY}. Remaining for family: {nodes_per_family_to_visit[best_family_id]}")
                     can_add_more = True # Μπορεί να χωράνε κι άλλοι

            # Αν δημιουργήθηκε δρομολόγιο, πρόσθεσέ το στη λύση
            if current_route:
                solution.append(current_route)
                print(f"Truck {truck_id} finalized with route: {current_route}, Load: {current_load}")
                truck_id += 1
            elif sum(nodes_per_family_to_visit.values()) > 0:
                 print(f"Warning: Could not add any more nodes, but {sum(nodes_per_family_to_visit.values())} required visits remain.")
                 break # Σταμάτα αν δεν μπορείς να προσθέσεις κόμβους αλλά μένουν απαιτήσεις


        if sum(nodes_per_family_to_visit.values()) > 0:
             print(f"\nERROR: Could not assign all required nodes. Remaining visits: {nodes_per_family_to_visit}")
             # Θα μπορούσε να γίνει χειρισμός σφάλματος ή να επιστραφεί μη εφικτή λύση
             return None # H αρχική λύση δεν είναι εφικτή

        print("\n--- Initial Solution Construction Complete ---")
        print(f"Initial Solution ({len(solution)} routes):")
        for i, r in enumerate(solution):
             print(f"  Route {i}: {r}")
        initial_cost = self.calculate_total_cost(solution)
        print(f"Initial Total Cost: {initial_cost}")

        # Έλεγχος εφικτότητας της αρχικής λύσης
        if not self.check_solution_feasibility(solution):
            print("ERROR: Initial solution is not feasible!")
            return None

        self.solution = solution
        self.total_cost = initial_cost
        return solution


    # --- Τελεστές Τοπικής Αναζήτησης ---

    def apply_2opt(self, route):
        """
        Εφαρμόζει τον τελεστή 2-Opt σε ένα δρομολόγιο για βελτίωση του κόστους του.
        Επιστρέφει το νέο δρομολόγιο και ένα flag αν έγινε βελτίωση.
        """
        if len(route) < 2:
            return route, False # Δεν γίνεται 2-opt σε δρομολόγιο με < 2 στάσεις

        improved = False
        best_route = route[:] # Ξεκίνα με το υπάρχον
        min_cost_change = 0

        # Πρόσθεσε προσωρινά το depot στην αρχή και το τέλος για ευκολία υπολογισμού
        temp_route = [self.DEPOT_NODE] + route + [self.DEPOT_NODE]

        # Βρόχοι για επιλογή των ακμών (i, i+1) και (j, j+1)
        # Το i πάει από 0 (depot) μέχρι len-3
        # Το j πάει από i+2 μέχρι len-2 (όπου len είναι το μήκος του temp_route)
        # π.χ., route = [A, B, C] => temp_route = [0, A, B, C, 0] (len=5)
        # i=0 (ακμή 0-A), j=2 (ακμή B-C) -> Ανταλλαγή -> [0, B, A, C, 0]
        # i=0 (ακμή 0-A), j=3 (ακμή C-0) -> Ανταλλαγή -> [0, C, B, A, 0]
        # i=1 (ακμή A-B), j=3 (ακμή C-0) -> Ανταλλαγή -> [0, A, C, B, 0]

        for i in range(len(temp_route) - 2):
            for j in range(i + 2, len(temp_route) - 1):
                # Αρχικές ακμές: (i, i+1) και (j, j+1)
                # Νέες ακμές:   (i, j) και (i+1, j+1)
                # Κόμβοι: node_i, node_i1 = temp_route[i], temp_route[i+1]
                #          node_j, node_j1 = temp_route[j], temp_route[j+1]
                node_i, node_i1 = temp_route[i], temp_route[i+1]
                node_j, node_j1 = temp_route[j], temp_route[j+1]

                original_cost = self.costs[node_i][node_i1] + self.costs[node_j][node_j1]
                new_cost = self.costs[node_i][node_j] + self.costs[node_i1][node_j1]
                cost_change = new_cost - original_cost

                if cost_change < min_cost_change: # Αν βρήκαμε βελτίωση
                    # Αντιστροφή του τμήματος μεταξύ i+1 και j
                    new_route_segment = temp_route[i+1 : j+1]
                    new_route_segment.reverse()
                    # Δημιουργία νέας προσωρινής διαδρομής
                    candidate_temp_route = temp_route[:i+1] + new_route_segment + temp_route[j+1:]

                    # Ενημέρωση καλύτερης αλλαγής και διαδρομής (αφαιρώντας τα depots)
                    min_cost_change = cost_change
                    best_route = candidate_temp_route[1:-1] # Αφαίρεσε τα depots
                    improved = True
                    # Σημείωση: Αυτό είναι "best improvement" μέσα στο 2-opt.
                    # Θα μπορούσε να γίνει "first improvement" κάνοντας return εδώ.

        # Μετά την εξέταση όλων των ζευγών, επέστρεψε την καλύτερη διαδρομή που βρέθηκε
        return best_route, improved


    def apply_relocate(self, current_solution):
        """
        Προσπαθεί να βρει την *καλύτερη* εφικτή κίνηση Relocate (μετακίνηση κόμβου
        από μια διαδρομή σε άλλη) που μειώνει το συνολικό κόστος.
        Εφαρμόζει την καλύτερη κίνηση αν βρεθεί και επιστρέφει True, αλλιώς False.
        """
        best_move = None # (node_id, from_route_idx, to_route_idx, insert_pos, cost_reduction)
        max_cost_reduction = 0

        solution = [r[:] for r in current_solution] # Δημιουργία τοπικού αντιγράφου

        for r1_idx in range(len(solution)):
            route1 = solution[r1_idx]
            if not route1: continue # Αγνοούμε κενά δρομολόγια

            for node_idx in range(len(route1)):
                node_to_move = route1[node_idx]
                node_demand = self.get_node_demand(node_to_move)

                # Υπολογισμός κόστους αφαίρεσης του κόμβου από τη route1
                prev_node = route1[node_idx - 1] if node_idx > 0 else self.DEPOT_NODE
                next_node = route1[node_idx + 1] if node_idx < len(route1) - 1 else self.DEPOT_NODE
                cost_removed = (self.costs[prev_node][node_to_move] +
                                self.costs[node_to_move][next_node] -
                                self.costs[prev_node][next_node])

                # Δοκιμή εισαγωγής σε *άλλα* δρομολόγια (r2)
                for r2_idx in range(len(solution)):
                    if r1_idx == r2_idx: continue # Δεν μετακινούμε στον ίδιο δρομολόγιο

                    route2 = solution[r2_idx]
                    route2_load = self.calculate_route_load(route2)

                    # Έλεγχος χωρητικότητας για τη route2
                    if route2_load + node_demand <= self.TRUCK_CAPACITY:
                        # Δοκιμή εισαγωγής σε κάθε πιθανή θέση στη route2 (και στην αρχή)
                        for insert_pos in range(len(route2) + 1):
                             prev_node_r2 = route2[insert_pos - 1] if insert_pos > 0 else self.DEPOT_NODE
                             next_node_r2 = route2[insert_pos] if insert_pos < len(route2) else self.DEPOT_NODE

                             cost_added = (self.costs[prev_node_r2][node_to_move] +
                                           self.costs[node_to_move][next_node_r2] -
                                           self.costs[prev_node_r2][next_node_r2])

                             cost_reduction = cost_removed - cost_added

                             if cost_reduction > max_cost_reduction:
                                 max_cost_reduction = cost_reduction
                                 best_move = (node_to_move, r1_idx, r2_idx, insert_pos, cost_reduction)

        # Αν βρέθηκε βελτιωτική κίνηση, εφάρμοσέ την στην αρχική λύση (self.solution)
        if best_move:
            node, r1i, r2i, pos, reduction = best_move
            print(f"  Applying Relocate: Move node {node} from route {r1i} to route {r2i} at pos {pos}. Cost reduction: {reduction:.2f}")

            # Αφαίρεση από το r1
            original_route1 = self.solution[r1i]
            original_route1.remove(node) # Πρέπει να είναι μοναδικός ο κόμβος

             # Προσθήκη στο r2
            original_route2 = self.solution[r2i]
            original_route2.insert(pos, node)

            # Ενημέρωση συνολικού κόστους
            self.total_cost -= reduction

            # Σημείωση: Δεν χρειάζεται να ελέγξουμε ξανά τα vl constraints, γιατί
            # η μετακίνηση ενός κόμβου δεν αλλάζει τον συνολικό αριθμό επισκέψεων
            # ανά οικογένεια σε ολόκληρη τη λύση. Μόνο η χωρητικότητα ελέγχθηκε.

            return True # Βρέθηκε και εφαρμόστηκε βελτίωση

        return False # Δεν βρέθηκε βελτιωτική κίνηση Relocate


    # --- Κύκλος Τοπικής Αναζήτησης ---
    def run_local_search(self, max_iterations=100):
        """
        Εκτελεί επαναληπτικά τους τελεστές τοπικής αναζήτησης (2-Opt, Relocate)
        μέχρι να μην υπάρχει περαιτέρω βελτίωση ή να φτάσει το όριο επαναλήψεων.
        """
        if not self.solution:
             print("Cannot run local search: No initial solution found.")
             return

        print("\n--- Starting Local Search ---")
        print(f"Initial Cost before LS: {self.total_cost:.2f}")

        iteration = 0
        improvement_found = True
        while improvement_found and iteration < max_iterations:
            iteration += 1
            improvement_found = False # Assume no improvement in this iteration
            print(f"\nLS Iteration {iteration}...")

            # 1. Intra-Route Optimization (2-Opt) για κάθε δρομολόγιο
            print("  Applying 2-Opt...")
            current_cost_before_2opt = self.calculate_total_cost(self.solution) # Για έλεγχο
            for r_idx in range(len(self.solution)):
                route_improved = True
                while route_improved: # Εφάρμοσε το 2-Opt επανειλημμένα στο ίδιο route αν βελτιώνεται
                    new_route, route_improved = self.apply_2opt(self.solution[r_idx])
                    if route_improved:
                        self.solution[r_idx] = new_route
                        improvement_found = True # Βρέθηκε βελτίωση γενικά
                        # print(f"    Improved route {r_idx} with 2-Opt.")
            cost_after_2opt = self.calculate_total_cost(self.solution)
            if cost_after_2opt < current_cost_before_2opt:
                 print(f"    Cost after 2-Opt: {cost_after_2opt:.2f} (Reduced by {current_cost_before_2opt - cost_after_2opt:.2f})")
            else:
                 print("    No cost reduction from 2-Opt in this pass.")


            # 2. Inter-Route Optimization (Relocate)
            print("  Applying Relocate (Best Improvement)...")
            relocate_improved = self.apply_relocate(self.solution) # Χρησιμοποιεί το self.solution
            if relocate_improved:
                improvement_found = True # Βρέθηκε βελτίωση γενικά
                print(f"    Cost after Relocate: {self.total_cost:.2f}")
            else:
                print("    No improving Relocate move found.")


            # (Προαιρετικά) Θα μπορούσε να προστεθεί και ο τελεστής Swap εδώ
            # swap_improved = self.apply_swap(self.solution)
            # if swap_improved:
            #     improvement_found = True


            if not improvement_found:
                print(f"No improvement found in iteration {iteration}. Stopping local search.")
                break

        print(f"\n--- Local Search Finished after {iteration} iterations ---")
        # Τελικός έλεγχος εφικτότητας (καλό είναι να υπάρχει)
        if not self.check_solution_feasibility(self.solution):
             print("ERROR: Solution became infeasible during local search!")
        final_cost = self.calculate_total_cost(self.solution)
        print(f"Final Solution Cost: {final_cost:.2f}")
        self.total_cost = final_cost


    # --- Εγγραφή Λύσης σε Αρχείο ---
    def write_solution_to_file(self, output_filename="solution.txt"):
        """
        Γράφει την τρέχουσα λύση (self.solution) στο αρχείο εξόδου
        με τη μορφή του solution_example.txt.
        """
        if not self.solution:
            print("No solution generated to write.")
            return

        print(f"\n--- Writing solution to {output_filename} ---")
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(f"Cost {int(round(self.total_cost))}\n") # Το κόστος ως ακέραιος
                for i, route in enumerate(self.solution):
                    # Μορφή: Route i: 0 -> node1 -> node2 -> ... -> 0
                    route_str = f"Route {i+1}: 0 -> {' -> '.join(map(str, route))} -> 0"
                    f.write(route_str + "\n")
            print("Solution written successfully.")
        except Exception as e:
            print(f"Error writing solution file: {e}")


# --- Κύριο Μέρος Προγράμματος ---
if __name__ == "__main__":
    instance_file = "fcvrp_P-n101-k4_10_3_3.txt" # Το αρχείο δεδομένων
    output_file = "solution_result.txt"      # Το αρχείο εξόδου
    random_seed = 42                           # Ένα από τα επιτρεπτά seeds

    # Δημιουργία αντικειμένου και φόρτωση δεδομένων
    fcvrp_instance = Fcvrp(instance_file, seed=random_seed)

    # 1. Κατασκευή αρχικής λύσης
    initial_solution = fcvrp_instance.construct_initial_solution()

    # 2. Εκτέλεση τοπικής αναζήτησης (αν υπήρχε αρχική λύση)
    if initial_solution:
        fcvrp_instance.run_local_search(max_iterations=50) # Όριο επαναλήψεων για ασφάλεια

        # 3. Εμφάνιση τελικής λύσης και κόστους
        print("\n--- Final Solution ---")
        final_solution = fcvrp_instance.solution
        for i, route in enumerate(final_solution):
            print(f"  Route {i}: {route}")
        print(f"Final Total Cost: {fcvrp_instance.total_cost:.2f}")

        # 4. Εγγραφή λύσης σε αρχείο
        fcvrp_instance.write_solution_to_file(output_file)

    else:
        print("\nExecution failed: Could not construct a feasible initial solution.")