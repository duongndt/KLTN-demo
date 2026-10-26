import csv, json, sys

HTTP = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}

res = json.load(open(sys.argv[1], encoding="utf-8"))
with open(sys.argv[2], encoding="utf-8") as f:
    all_ops = list(csv.DictReader(f))

flagged = []
for r in res:
    if "api1" not in r["code"]:
        continue
    p = r["path"]
    if len(p) < 2 or p[0] != "paths":
        continue
    path = p[1]
    if len(p) >= 3 and p[2] in HTTP:
        ops = [(p[2].upper(), path)]
    else:
        ops = [(o["method"], o["path"]) for o in all_ops if o["path"] == path]
    for op in ops:
        if op not in flagged:
            flagged.append(op)

with open(sys.argv[3], "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["method", "path"])
    w.writerows(flagged)
print("Số operation bị cảnh báo API1:", len(flagged))