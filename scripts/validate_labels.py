#!/usr/bin/env python3
"""
Validate JSONL against schema, compute Fleiss' kappa overall and per mismatch_type,
ensure >=0.8 overall agreement and report class balance.
"""
import json, sys, math
from collections import Counter, defaultdict
from jsonschema import Draft202012Validator

LABELS = ["equivalent","not_equivalent","uncertain"]

def fleiss_kappa(label_matrix):
    # label_matrix: list of counts per item [n_cat] where sum(row)=n_raters
    N = len(label_matrix); n = sum(label_matrix[0])
    p = [sum(row[j] for row in label_matrix)/(N*n) for j in range(len(label_matrix[0]))]
    P = [ (sum(c*c for c in row) - n) / (n*(n-1)) for row in label_matrix ]
    Pbar = sum(P)/N
    Pe = sum(pi*pi for pi in p)
    return (Pbar - Pe) / (1 - Pe) if (1-Pe) else 1.0

def main(jsonl_path, schema_path):
    schema = json.load(open(schema_path))
    validator = Draft202012Validator(schema)
    total, per_type = 0, defaultdict(list)
    class_counts = Counter()
    errors = []

    with open(jsonl_path) as f:
        for ln, line in enumerate(f, 1):
            if not line.strip(): continue
            obj = json.loads(line)
            for err in validator.iter_errors(obj):
                errors.append(f"L{ln}: {err.message}")
            total += 1
            labels = [lab["label"] for lab in obj["labels"]]
            class_counts.update(labels)
            row = [labels.count(lbl) for lbl in LABELS]
            per_type[obj["mismatch_type"]].append(row)

    if errors:
        print("SCHEMA ERRORS:")
        print("\n".join(errors)); sys.exit(2)

    # Overall kappa
    all_rows = [row for rows in per_type.values() for row in rows]
    kappa_all = fleiss_kappa(all_rows) if all_rows else float("nan")
    print(f"Items: {total}  Overall Fleiss' kappa: {kappa_all:.3f}")
    for t, rows in per_type.items():
        k = fleiss_kappa(rows)
        print(f"  {t}: kappa={k:.3f}  n={len(rows)}")

    print("Label distribution:", dict(class_counts))

    if kappa_all < 0.8:
        print("FAIL: overall kappa < 0.8"); sys.exit(3)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: validate_labels.py <dataset.jsonl> <schema.json>"); sys.exit(1)
    main(sys.argv[1], sys.argv[2])
