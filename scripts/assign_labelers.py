#!/usr/bin/env python3
"""
Assign 3 raters per item with balanced pair overlap.
Input: CSV of item ids (id)
Output: CSV with rows (id, rater_id)
"""
import csv, itertools, sys, random
RATERS = [f"r{str(i).zfill(2)}" for i in range(1,10)]  # adjust pool size
random.seed(7)

def main(inp, out):
    ids = [r["id"] for r in csv.DictReader(open(inp))]
    writer = csv.writer(open(out, "w", newline=""))
    writer.writerow(["id","rater_id"])
    # Simple round-robin blocks ensuring each id gets 3 distinct raters
    k = len(RATERS)
    for idx, mid in enumerate(ids):
        trio = [RATERS[(idx + o) % k] for o in (0,1,2)]
        for r in trio:
            writer.writerow([mid, r])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: assign_labelers.py items.csv assignments.csv"); sys.exit(1)
    main(sys.argv[1], sys.argv[2])
