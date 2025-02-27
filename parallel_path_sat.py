"""
Parallel Path-Based 3-SAT Solver

This Python class implements a **path-based approach** to solving the **3-SAT problem** efficiently.
Instead of traditional backtracking, it tracks variable assignments as **immutable paths**, ensuring fast deduplication
and leveraging structured variable scattering to improve clause distribution.

Features:
- **Path-based expansion**: Tracks SAT assignments without recursive backtracking.
- **Fast UNSAT detection**: Eliminates invalid paths early for quick failure cases.
- **Variable scattering**: Preprocesses clauses to balance variable occurrence distribution.
- **DNF extraction**: Generates a valid Disjunctive Normal Form (DNF) representation if SAT is found.
- **Immutable tuple-based paths**: Ensures efficient lookup and deduplication.

This solver is designed for efficiency and can be used for both **SAT solving** and **DNF generation**.

Usage:
    sat_solver = ParallelPathSAT()
    result = sat_solver.solve(cnf_clauses, generate_dnf=True)
    if result:
        print("SAT")
        if sat_solver.dnf:
            print("DNF Representation:", sat_solver.dnf)
    else:
        print("UNSAT")

Author: Tomio Kobayashi
Version: 1.0.1
Last Updated: 2/28/2025

"""


import random

class ParallelPathSAT:

    def __init__(self):
        self.dnf = None
        
    def preprocess_scatter_variables(self, clauses):
        """
        Shuffles and rearranges CNF clauses to evenly distribute variables and signs.
        This prevents over-concentration of specific variables in early clauses.
        """
        # Step 1: Count variable occurrences
        var_counts = {}
        for clause in clauses:
            for lit in clause:
                var = abs(lit)
                if var not in var_counts:
                    var_counts[var] = [0, 0]  # [positive_count, negative_count]
                if lit > 0:
                    var_counts[var][0] += 1
                else:
                    var_counts[var][1] += 1
    
        # Step 2: Sort clauses by the diversity of variables
        def clause_diversity(clause):
            """
            Measures diversity as a mix of unique variables and balanced positive/negative signs.
            """
            unique_vars = len(set(abs(lit) for lit in clause))
            balance_score = sum(1 if lit > 0 else -1 for lit in clause)  # Closer to 0 is balanced
            return unique_vars, abs(balance_score)  # Maximize unique vars, minimize imbalance
    
        clauses.sort(key=clause_diversity, reverse=True)  # Prioritize diverse & balanced clauses
    
        # Step 3: Shuffle in chunks to maintain diversity while allowing randomness
        chunk_size = max(1, len(clauses) // 4)  # Divide into 4 chunks
        for i in range(0, len(clauses), chunk_size):
            random.shuffle(clauses[i:i + chunk_size])  # Shuffle within each chunk
    
        return clauses

    def solve(self, clauses, generate_dnf=False):
        """
        Uses tuples for path tracking, ensuring immutability and fast deduplication.
        """
        clauses = self.preprocess_scatter_variables(clauses)
        variables = sorted({abs(lit) for clause in clauses for lit in clause})  # Extract sorted variables
        var_index = {var: i for i, var in enumerate(variables)}  # Map variables to tuple index
        num_vars = len(var_index)
    
        paths = {tuple([0] * num_vars)}  # Initial path (all variables unassigned)
        
        for clause in clauses:
            new_paths = set()  # Store unique new paths
    
            for path in paths:
                local_new_paths = set()
    
                for lit in clause:
                    var_idx = var_index[abs(lit)]
                    sign = 1 if lit > 0 else -1
    
                    if path[var_idx] == -sign:  # Conflict: discard this path
                        continue
                    
                    # if path[var_idx] == 0:  # Unassigned variable, create a new path
                    new_path = list(path)  # Convert tuple to list for modification
                    new_path[var_idx] = sign
                    local_new_paths.add(tuple(new_path))  # Convert back to tuple for O(1) lookup
    
                if local_new_paths:
                    new_paths.update(local_new_paths)
    
            # **Drop Old Paths Explicitly**  
            paths = new_paths  # Only retain the new unique paths
            # print("len(paths)", len(paths))
            if not paths:  # If all paths are invalidated, return UNSAT
                return False  
        if generate_dnf:
            self.dnf = []
            index_var = {v: k for k, v in var_index.items()}
            for p in new_paths:
                dnf_clause = []
                for i, pp in enumerate(p):
                    # print(pp)
                    if pp != 0:
                        dnf_clause.append(index_var[i] if pp == 1 else index_var[i]*-1)
                
                # print("dnf_clause", dnf_clause)
                if dnf_clause:
                    self.dnf.append(dnf_clause)
        return True  # If at least one valid path remains, return SAT

# Example CNF Formula (SAT Example)
cnf_formula = [
    [1, -3, 4],  # 1 OR ¬3 OR 4
    [-1, 2, 3],  # ¬1 OR 2 OR 3
    [3, -4, -2], # 3 OR ¬4 OR ¬2
    [-1, -2, 4], # ¬1 OR ¬2 OR 4
    [5, 5, 5],   # 5 appears only in one polarity -> will be replaced with dummy
    [6, 6, -6]   # Becomes {6, -6} -> no change (not removed)
]

# Generate CNFs with different sizes
# cnf_formula = generate_cnf(5, 5)   # 10 clauses, 5 variables
# cnf_formula = generate_cnf(5, 10)   # 10 clauses, 5 variables
# cnf_formula = generate_cnf(10, 20) # 20 clauses, 10 variables
# cnf_formula = generate_cnf(15, 30) # 30 clauses, 15 variables
cnf_formula = generate_cnf(20, 60) # 20 clauses, 60 variables
# cnf_formula = generate_cnf(30, 100) # 30 clauses, 15 variables
# cnf_formula = generate_cnf(40, 100) # 30 clauses, 15 variables

cnf_formula = [[4, -18, 19], [3, 18, -5], [-5, -8, -15], [-20, 7, -16], [10, -13, -7], [-12, -9, 17], [17, 19, 5], [-16, 9, 15], [11, -5, -14], 
       [18, -10, 13], [-3, 11, 12], [-6, -17, -8], [-18, 14, 1], [-19, -15, 10], [12, 18, -19], [-8, 4, 7], [-8, -9, 4], [7, 17, -15], 
       [12, -7, -14], [-10, -11, 8], [2, -15, -11], [9, 6, 1], [-11, 20, -17], [9, -15, 13], [12, -7, -17], [-18, -2, 20], [20, 12, 4], 
       [19, 11, 14], [-16, 18, -4], [-1, -17, -19], [-13, 15, 10], [-12, -14, -13], [12, -14, -7], [-7, 16, 10], [6, 10, 7], [20, 14, -16], 
       [-19, 17, 11], [-7, 1, -20], [-5, 12, 15], [-4, -9, -13], [12, -11, -7], [-5, 19, -8], [1, 16, 17], [20, -14, -15], [13, -4, 10], 
       [14, 7, 10], [-5, 9, 20], [10, 1, -19], [-16, -15, -1], [16, 3, -11], [-15, -10, 4], [4, -15, -3], [-10, -16, 11], [-8, 12, -5], 
       [14, -6, 12], [1, 6, 11], [-13, -5, -1], [-7, -2, 12], [1, -20, 19], [-2, -13, -8], [15, 18, 4], [-11, 14, 9], [-6, -15, -2], 
       [5, -12, -15], [-6, 17, 5], [-13, 5, -19], [20, -1, 14], [9, -17, 15], [-5, 19, -18], [-12, 8, -10], [-18, 14, -4], [15, -9, 13], 
       [9, -5, -1], [10, -19, -14], [20, 9, 4], [-9, -2, 19], [-5, 13, -17],[2, -10, -18], [-18, 3, 11], [7, -9, 17],[-15, -6, -3],
       [-2, 3, -13], [12, 3, -2], [-2, -3, 17], [20, -15, -16], [-5, -17, -19], [-20, -18, 11], [-9, 1, -5], [-19, 9, 17], [12, -2, 17]
      ]
         
sat_solver = ParallelPathSAT()
print("SAT Result:", "SAT" if sat_solver.solve(cnf_formula, generate_dnf=False) else "UNSAT")

# sat_solver.dnf