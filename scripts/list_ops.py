import csv, json, sys
import yaml

HTTP = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f) if path.endswith(".json") else yaml.safe_load(f)

spec = load(sys.argv[1])
ops = [(m.upper(), p) for p, item in spec["paths"].items()
       for m in item if m in HTTP]
print("Tổng số operation:", len(ops))
with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["method", "path"])
    w.writerows(ops)