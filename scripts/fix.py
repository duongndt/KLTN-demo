
from pathlib import Path
import re
import shutil
import sys
import yaml

HTTP_METHODS = {
    "get", "post", "put", "delete",
    "patch", "options", "head", "trace"
}


def normalize_name(name):
    name = str(name or "").strip()
    if name.startswith("{"):
        name = name[1:]
    if name.endswith("}"):
        name = name[:-1]
    return name.strip()


def main():
    source = Path(
        sys.argv[1] if len(sys.argv) > 1
        else "data/vapi-openapi.yaml"
    )

    if not source.exists():
        sys.exit(f"Không tìm thấy file: {source}")

    backup = source.with_suffix(source.suffix + ".path.bak")
    if not backup.exists():
        shutil.copy2(source, backup)
        print(f"Đã sao lưu: {backup}")

    with source.open("r", encoding="utf-8-sig") as f:
        doc = yaml.safe_load(f)

    paths = doc.get("paths", {})
    fixes = []

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        names = re.findall(r"\{([^{}]+)\}", path)
        if not names:
            continue

        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue

            params = operation.get("parameters") or []
            if not isinstance(params, list):
                print(f"CẢNH BÁO: parameters không phải list: {method} {path}")
                continue

            # Sửa tên tham số path trực tiếp trong operation.
            for param in params:
                if not isinstance(param, dict):
                    continue
                if param.get("in") == "path":
                    old = param.get("name", "")
                    new = normalize_name(old)
                    if new != old:
                        param["name"] = new
                        fixes.append(
                            f"Sửa {method.upper()} {path}: {old} -> {new}"
                        )
                    param["required"] = True

            # Tính các tham số được khai báo ở cấp path và operation.
            declared = set()
            unresolved_refs = []

            for param in (
                (path_item.get("parameters") or []) + params
            ):
                if not isinstance(param, dict):
                    continue

                if "$ref" in param:
                    ref = param["$ref"]
                    if ref.startswith("#/components/parameters/"):
                        key = ref.rsplit("/", 1)[-1]
                        component = (
                            doc.get("components", {})
                               .get("parameters", {})
                               .get(key, {})
                        )
                        if component.get("in") == "path":
                            declared.add(
                                normalize_name(component.get("name"))
                            )
                        else:
                            unresolved_refs.append(ref)
                    else:
                        unresolved_refs.append(ref)
                    continue

                if param.get("in") == "path":
                    declared.add(normalize_name(param.get("name")))

            for name in names:
                if name in declared:
                    continue

                params.append({
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": f"Path parameter {name}"
                })
                declared.add(name)
                fixes.append(
                    f"Bổ sung {name} cho {method.upper()} {path}"
                )

            if params:
                operation["parameters"] = params

            if unresolved_refs:
                print(
                    f"CẦN KIỂM TRA $ref tại {method.upper()} {path}: "
                    f"{unresolved_refs}"
                )

    temp = source.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(
            doc, f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False
        )

    # Đảm bảo file tạm vẫn parse được trước khi thay file gốc.
    with temp.open("r", encoding="utf-8") as f:
        yaml.safe_load(f)

    temp.replace(source)

    print(f"\nĐã cập nhật {source}")
    print(f"Tổng số thay đổi: {len(fixes)}")
    for item in fixes:
        print("-", item)


if __name__ == "__main__":
    main()
