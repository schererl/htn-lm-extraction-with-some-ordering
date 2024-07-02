import pulp

def print_variables_and_constraints(lp):
    print("Variables:")
    for v in lp.variables():
        if v.varValue is not None and v.varValue >= 1:
            print(f"name={v.name} bounds=({v.lowBound}, {v.upBound}) value={v.varValue}")

nodes = ['A', 'X', 'Z', 'B', 'M3', 'M2', 'M1', 'S', 'T', 'C']
node_types = {
    'A': 'AND', 
    'X': 'OR',
    'Y': 'OR',
    'B': 'AND',
    'Z': 'OR',
    'M3': 'AND',
    'M1': 'AND',
    'M2': 'AND',
    'T': 'OR',
    'S': 'OR',
    'C': 'AND'
}

predecessors = {
    'A': ['X'], 
    'X': [],
    'Z': ['A'],
    'B': ['Z'],
    'M3': ['A'],
    'S': ['M3'],
    'M1': ['S', 'B', 'C'],
    'M2': ['B'],
    'T': ['M1', 'M2'],
    'C': []
}

# reachable constraints
reachable_nodes = {
    'A': 1, 
    'X': 1,
    'Y': 1,
    'B': 1,
    'Z': 1,
    'M3': 1,
    'M1': 1,
    'M2': 1,
    'T': 1,
    'S': 1,
    'C': 1,
}

# nodes = ['B', 'M1', 'M2', 'T']
# node_types = {
#     'B': 'AND',
#     'M1': 'AND',
#     'M2': 'AND',
#     'T': 'OR'
# }

# predecessors = {
#     'B': [],
#     'M1': ['B'],
#     'M2': ['B'],
#     'T': ['M1', 'M2'],
# }

# # reachable constraints
# reachable_nodes = {
#     'B': 1,
#     'M1': 1,
#     'M2': 0,
#     'T': 1
# }

lp_problem = pulp.LpProblem("Landmark_Propagation", pulp.LpMinimize)
landmarks = {f"{n1}": {f"{n2}": pulp.LpVariable(f"L_({n1},{n2})", 0, 1, pulp.LpBinary) for n2 in nodes} for n1 in nodes}

for lm_dict in landmarks.values():
    for lm_var in lm_dict.values():
        lm_var.setInitialValue(1, check=True)

# initialization: Nodes with no predecessors
for node in nodes:
    if len(predecessors[node]) == 0:
        for lm in nodes:
            landmarks[node][lm].upBound=0
            landmarks[node][lm].lowBound=0
    landmarks[node][node].upBound=1
    landmarks[node][node].lowBound=1
# initialization: unreachable nodes cannot be landmarks of othe nodes neither can have landmarks    
for n1 in nodes:
    if reachable_nodes[n1] == 0:
        print(f'{n1} not reachable')
        for n2 in nodes:
            landmarks[n1][n2].lowBound = 0
            landmarks[n1][n2].upBound = 0
    else:
        for n2 in nodes:
            if reachable_nodes[n2] == 0:
                landmarks[n1][n2].lowBound = 0
                landmarks[n1][n2].upBound = 0
                
        
M = 1000
# get and-or landmarks
for node in nodes:
    # adding constraints to the unreachable nodes lead to unsolvable tasks
    if reachable_nodes[node]==0:
        continue
    print(f'\n\nNODE {node}')
    valid_predecessors=[p for p in predecessors[node] if reachable_nodes[p]==1]
    for lm in nodes:
        if lm == node:
            continue
        
        
        if node_types[node] == 'OR':
            if len(predecessors[node])>0:
                constraint = landmarks[node][lm] >= pulp.lpSum([landmarks[pred][lm] for pred in valid_predecessors]) - len(valid_predecessors) + 1
                lp_problem += constraint
                print(f'\nlm {lm}:\t{landmarks[node][lm]} >= sum({[landmarks[pred][lm] for pred in valid_predecessors]}) - {len(valid_predecessors)} + 1')
            
            for pred in valid_predecessors:
                # se o predecessor nao ser valido, o valor vai ser arbitrariamente grande
                constraint = landmarks[node][lm] <= landmarks[pred][lm] +  M * (1-reachable_nodes[pred])
                lp_problem += constraint
                print(f'or\t\t{landmarks[node][lm]} <= {landmarks[pred][lm]} + M * (1-{reachable_nodes[pred]}) \t:{node}({landmarks[node][lm].lowBound},{landmarks[node][lm].upBound})|{pred}({landmarks[pred][lm].lowBound},{landmarks[pred][lm].upBound}))')
            
            
        else:  # AND node
            if len(predecessors[node])>0:
                constraint = landmarks[node][lm] <= pulp.lpSum([landmarks[pred][lm] for pred in valid_predecessors])
                lp_problem += constraint
                print(f'\nlm {lm}:\t{landmarks[node][lm]} <= sum({[landmarks[pred][lm] for pred in valid_predecessors]})')
            
            for pred in valid_predecessors:
                # se o predecessor for falso o valor vai ser arbitrarimente pequeno
                constraint = landmarks[node][lm] >= landmarks[pred][lm] - M * (1-reachable_nodes[pred])
                print(f'and\t\t{landmarks[node][lm]} >= {landmarks[pred][lm]} - M * (1-{reachable_nodes[pred]}) \t:{node}({landmarks[node][lm].lowBound},{landmarks[node][lm].upBound})|{pred}({landmarks[pred][lm].lowBound},{landmarks[pred][lm].upBound}))')
                lp_problem += constraint
                      

# Objective function: Minimize the sum of all landmarks
lp_problem += -pulp.lpSum([landmarks[n1][n2] for n2 in nodes for n1 in nodes])
#lp_problem += -pulp.lpSum([landmarks['T'][n] for n])

result = lp_problem.solve()
if lp_problem.status == pulp.LpStatusOptimal:
    print_variables_and_constraints(lp_problem)
else:
    print("The problem is not solvable.")
