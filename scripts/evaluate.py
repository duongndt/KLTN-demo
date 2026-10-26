import csv, sys

def read(path):
    with open(path, encoding="utf-8") as f:
        return [(r["method"].upper(), r["path"]) for r in csv.DictReader(f)]

truth = set(read(sys.argv[1]))
flagged_list = read(sys.argv[2])
all_ops = read(sys.argv[3])
flagged = set(flagged_list)

tp, fp, fn = flagged & truth, flagged - truth, truth - flagged
p = len(tp) / len(flagged) if flagged else 0
r = len(tp) / len(truth) if truth else 0
f1 = 2 * p * r / (p + r) if p + r else 0

print(f"TP={len(tp)} FP={len(fp)} FN={len(fn)}")
print(f"Precision={p:.2f} Recall={r:.2f} F1={f1:.2f}")
print(f"Thu hẹp: {len(flagged)}/{len(all_ops)} = {len(flagged)/len(all_ops):.1%}")
for op in sorted(truth):
    pos = flagged_list.index(op) + 1 if op in flagged else None
    print("Vị trí xếp hạng", op, "->", pos)
print("FN:", sorted(fn))
print("FP:", sorted(fp))
