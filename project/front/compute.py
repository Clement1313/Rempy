import requests
import os

BASE_URL = "http://back:8000"
PUBLIC_HOST = "http://localhost:8000"


def run_benchmark(image_path):
    if not image_path or not os.path.exists(image_path):
        return "Error: no image selected or file not found"

    mask_path = "media/inputs/masks/mask.png"
    if not os.path.exists(mask_path):
        return f"Error: mask not found at {mask_path}"

    with open(image_path, "rb") as img, open(mask_path, "rb") as mask:
        files = {"image_file": img, "mask_file": mask}
        data = {"name": "default"}

        resp = requests.post(f"{BASE_URL}/api/images/", files=files, data=data)
    if not resp.ok:
        return f"Error {resp.status_code}: {resp.text}"

    image_id = resp.json()["id"]

    bench_payload = {"name": f"default", "image_ids": [image_id]}

    bench_resp = requests.post(f"{BASE_URL}/api/benchmarks/", json=bench_payload)

    bench_resp.raise_for_status()
    return bench_resp.json()


# res = run_benchmark ('media/inputs/images/img.png')
# print(res)
