import csv, json, re, sys
import yaml

try:
    from openapi_spec_validator import validate
except ImportError:                       # bản cũ của thư viện
    from openapi_spec_validator import validate_spec as validate

HTTP = ["get", "put", "post", "delete", "patch"]
WRITE = {"post", "put", "patch", "delete"}
W1, W2, W3 = 0.5, 0.25, 0.25              # đặt cố định TRƯỚC khi chạy thực nghiệm
ID_SCORE = {"numerical": 1.0, "personal": 0.8, "string": 0.6,
            "array": 0.6, "other": 0.5, "uuid": 0.3}
LOC_SCORE = {"path": 1.0, "query": 1.0, "body": 0.6, "header": 0.4}
TECH = {"numerical": "Dò quét không tri thức tiên nghiệm",
        "array": "Chèn thêm vào danh sách"}
ID_WORDS = {"name", "filename", "group", "key", "phone", "email"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f) if path.endswith(".json") else yaml.safe_load(f)


def resolve(spec, obj):
    """Giải quyết $ref nội bộ (dạng '#/...')."""
    for _ in range(10):
        if not (isinstance(obj, dict) and str(obj.get("$ref", "")).startswith("#/")):
            break
        node = spec
        for part in obj["$ref"][2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            node = node.get(part, {}) if isinstance(node, dict) else {}
        obj = node
    return obj


def is_identifier(name, desc):
    low = name.lower()
    if re.search(r"(_id|Id|ID)$", name) or low in ("id", "uuid", "guid"):
        return True
    if low.endswith(("uuid", "guid")) or low in ID_WORDS:
        return True
    return bool(re.search(r"\b(id|uuid|guid|identifier)\b", desc or "", re.I))


def id_type(name, schema):
    t, fmt, low = schema.get("type"), schema.get("format", ""), name.lower()
    if t == "array":
        return "array"
    if fmt == "uuid" or "uuid" in low or "guid" in low:
        return "uuid"
    if t in ("integer", "number"):
        return "numerical"
    if t == "string" and re.search(r"email|phone", low):
        return "personal"
    if t == "string":
        return "string"
    return "other"


def collect_params(spec, item, op):
    params = {}
    for src in (item.get("parameters", []), op.get("parameters", [])):
        for p in src:
            p = resolve(spec, p)
            if p.get("name"):
                params[(p["name"], p.get("in"))] = p
    out = [(n, loc, p.get("description", ""), resolve(spec, p.get("schema", {})))
           for (n, loc), p in params.items()]
    body = resolve(spec, op.get("requestBody", {}))
    for media in body.get("content", {}).values():
        schema = resolve(spec, media.get("schema", {}))
        for pname, ps in schema.get("properties", {}).items():
            out.append((pname, "body", "", resolve(spec, ps)))
    return out


def scan(spec, assume_auth=False):
    rows = []
    for path, item in spec.get("paths", {}).items():
        item = resolve(spec, item)
        methods = [m for m in HTTP if m in item]
        writes = sum(m in WRITE for m in methods)
        for m in methods:
            op = item[m]
            has_auth = bool(op.get("security", spec.get("security", [])))
            if not has_auth and not assume_auth:
                continue
            best = None
            for name, loc, desc, schema in collect_params(spec, item, op):
                if not is_identifier(name, desc):
                    continue
                t = id_type(name, schema)
                score = (W1 * ID_SCORE[t] + W2 * LOC_SCORE.get(loc, 0.5)
                         + W3 * min(1.0, writes / 3))
                if best is None or score > best[0]:
                    best = (score, name, t)
            if best:
                score, name, t = best
                level = ("Cao" if score >= 0.67
                         else "Trung bình" if score >= 0.34 else "Thấp")
                rows.append({"method": m.upper(), "path": path,
                             "score": round(score, 2), "level": level,
                             "technique": TECH.get(t, "Dò quét có tri thức tiên nghiệm"),
                             "param": name})
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    spec_path, out_path = args[0], args[1]
    spec = load(spec_path)
    try:
        validate(spec)
    except Exception as e:
        sys.exit(f"Đặc tả không hợp lệ: {e}")
    rows = scan(spec, assume_auth="--assume-auth" in sys.argv)
    rows.sort(key=lambda r: -r["score"])
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["method", "path", "score",
                                          "level", "technique", "param"])
        w.writeheader()
        w.writerows(rows)
    print(f"Đã cảnh báo {len(rows)} operation -> {out_path}")


if __name__ == "__main__":
    main()