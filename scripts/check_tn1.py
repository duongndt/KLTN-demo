import csv, sys

EXPECTED = {
    ("GET", "/orders/{orderId}"): True,
    ("GET", "/vehicles/{vehicleId}/location"): True,
    ("POST", "/batch/orders"): True,
    ("GET", "/health"): False,
    ("GET", "/products"): False,
    ("GET", "/public/{itemId}"): False,
}

with open(sys.argv[1], encoding="utf-8") as f:
    flagged = {(r["method"].upper(), r["path"]) for r in csv.DictReader(f)}

dung = 0
for op, should in EXPECTED.items():
    actual = op in flagged
    ok = actual == should
    dung += ok
    print(f"{op[0]:5} {op[1]:36} kỳ vọng: {'cảnh báo' if should else 'bỏ qua':8} "
          f"thực tế: {'cảnh báo' if actual else 'bỏ qua':8} -> {'Đúng' if ok else 'SAI'}")
extra = flagged - set(EXPECTED)
if extra:
    print("Operation ngoài danh sách kỳ vọng bị cảnh báo:", sorted(extra))
print(f"Kết quả: {dung}/{len(EXPECTED)} operation đúng")