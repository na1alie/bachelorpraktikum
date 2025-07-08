import json

PREC_RECALL = '/home/natalie/Bachelorprojekt/evaluation/precision_recall.json'

# Load JSON
with open(PREC_RECALL, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Group by (method, top_n)
results_by_method_top_n = {}

for item in data:
    method = item["method"]
    top_n = item["top_n"]
    precision = item["precision"]
    recall = item["recall"]

    key = (method, top_n)

    if key not in results_by_method_top_n:
        results_by_method_top_n[key] = {"precisions": [], "recalls": []}

    results_by_method_top_n[key]["precisions"].append(precision)
    results_by_method_top_n[key]["recalls"].append(recall)

# Calculate averages
for (method, top_n), values in sorted(results_by_method_top_n.items()):
    avg_precision = sum(values["precisions"]) / len(values["precisions"])
    avg_recall = sum(values["recalls"]) / len(values["recalls"])
    print(f"Method: {method} | Top N = {top_n}")
    print(f"  Average Precision: {avg_precision:.3f}")
    print(f"  Average Recall: {avg_recall:.3f}")
    print()