import csv, sys

def read(p):
    with open(p, encoding="utf-8") as f:
        return {(r["method"].upper(), r["path"]) for r in csv.DictReader(f)}

gt, ops = read(sys.argv[1]), read(sys.argv[2])
for op in sorted(gt):
    print("CÓ trong spec     " if op in ops else "KHÔNG có trong spec", op)