import json
from z3 import *

# -------------------------
# Load JSON
# -------------------------
with open("tasks.json", "r") as f:
    data = json.load(f)

num_nodes = data["num_nodes"]
tasks = data["tasks"]
n = len(tasks)

# -------------------------
# Create solver
# -------------------------
solver = Solver()

# -------------------------
# Decision Variables
# -------------------------

# Start times
start = [Int(f"start_{i}") for i in range(n)]

# Node assignment
node = [Int(f"node_{i}") for i in range(n)]

# -------------------------
# Task constraints
# -------------------------

for i, task in enumerate(tasks):

    release = task["release_time"]
    wcet = task["wcet"]
    deadline = task["deadline"]
    allowed = task["allowed_nodes"]

    # Release time
    solver.add(start[i] >= release)

    # Deadline
    solver.add(start[i] + wcet <= deadline)

    # Node must be valid index
    solver.add(node[i] >= 0, node[i] < num_nodes)

    # Node must be in allowed_nodes
    allowed_constraints = [node[i] == k for k in allowed]
    solver.add(Or(allowed_constraints))


# -------------------------
# Non-overlap constraints
# -------------------------

for i in range(n):
    for j in range(i + 1, n):

        wcet_i = tasks[i]["wcet"]
        wcet_j = tasks[j]["wcet"]

        same_node = node[i] == node[j]

        no_overlap = Or(
            start[i] + wcet_i <= start[j],
            start[j] + wcet_j <= start[i]
        )

        solver.add(Implies(same_node, no_overlap))


# -------------------------
# Solve
# -------------------------

if solver.check() == sat:
    model = solver.model()
    print("\nFeasible schedule found:\n")

    for i in range(n):
        assigned_node = model[node[i]].as_long()
        start_time = model[start[i]].as_long()
        finish_time = start_time + tasks[i]["wcet"]

        print(f"Task {i}:")
        print(f"  Node   : {assigned_node}")
        print(f"  Start  : {start_time}")
        print(f"  Finish : {finish_time}")
        print()
else:
    print("No feasible schedule found.")