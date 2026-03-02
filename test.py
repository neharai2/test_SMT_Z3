import json
from z3 import *

# -------------------------
# Load JSON
# -------------------------
with open("example_100T_fixed.json", "r") as f:
    data = json.load(f)

jobs = data["application"]["jobs"]
platform_nodes = data["platform"]["nodes"]

# Only non-router nodes
compute_nodes = [n["id"] for n in platform_nodes if not n["is_router"]]

num_nodes = len(compute_nodes)
n = len(jobs)

# Map real node IDs to 0..(num_nodes-1) for solver indexing
node_id_to_index = {nid: idx for idx, nid in enumerate(sorted(compute_nodes))}
index_to_node_id = {idx: nid for nid, idx in node_id_to_index.items()}

# -------------------------
# Create solver
# -------------------------
solver = Solver()

# -------------------------
# Decision Variables
# -------------------------

start = [Int(f"start_{i}") for i in range(n)]
node = [Int(f"node_{i}") for i in range(n)]

# -------------------------
# Job constraints
# -------------------------

for i, job in enumerate(jobs):

    wcet = job["wcet_fullspeed"]
    deadline = job["deadline"]
    allowed_real_nodes = job["can_run_on"]

    # Convert allowed real node IDs to solver indices
    allowed_indices = [
        node_id_to_index[nid]
        for nid in allowed_real_nodes
        if nid in node_id_to_index
    ]

    # Start time constraint
    solver.add(start[i] >= 0)

    # Deadline constraint
    solver.add(start[i] + wcet <= deadline)

    # Node index bounds
    solver.add(node[i] >= 0, node[i] < num_nodes)

    # Node must be in allowed list
    solver.add(Or([node[i] == k for k in allowed_indices]))

# -------------------------
# Non-overlap constraints
# -------------------------

for i in range(n):
    for j in range(i + 1, n):

        wcet_i = jobs[i]["wcet_fullspeed"]
        wcet_j = jobs[j]["wcet_fullspeed"]

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

    output_schedule = {
        "schedule": []
    }

    for i in range(n):

        job_id = jobs[i]["id"]
        assigned_index = model[node[i]].as_long()
        assigned_real_node = index_to_node_id[assigned_index]

        start_time = model[start[i]].as_long()
        wcet = jobs[i]["wcet_fullspeed"]
        deadline = jobs[i]["deadline"]
        finish_time = start_time + wcet

        output_schedule["schedule"].append({
            "job_id": job_id,
            "assigned_node": assigned_real_node,
            "start_time": start_time,
            "wcet_fullspeed": wcet,
            "finish_time": finish_time,
            "deadline": deadline
        })

    # Write output JSON
    with open("schedule_output.json", "w") as f:
        json.dump(output_schedule, f, indent=4)

    print("Feasible schedule found. Output written to schedule_output.json")

else:
    print("No feasible schedule found.")