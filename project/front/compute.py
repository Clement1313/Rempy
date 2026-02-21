import requests
import os

BASE_URL = "http://back:8000"
PUBLIC_HOST = "http://localhost:8000"


def run_benchmark(image_path, mask_url, threshold):
    if not image_path or not os.path.exists(image_path):
        return "Error: no image selected or file not found"
    if not mask_url:
        return "Error: no mask"

    mask_file_resp = requests.get(f"{BASE_URL}{mask_url}")

    if not mask_file_resp.ok:
        return f"Error downloading mask"

    with open(image_path, "rb") as img:
        files = {
            "image_file": img,
            "mask_file": ("mask.png", mask_file_resp.content),
        }

        resp = requests.post(
            f"{BASE_URL}/api/images/",
            files=files,
            data={"name": "default"},
        )

    if not resp.ok:
        return f"Error {resp.status_code}: {resp.text}"

    image_id = resp.json()["id"]

    bench_resp = requests.post(
        f"{BASE_URL}/api/benchmarks/",
        json={"name": "default", "image_ids": [image_id], "threshold": threshold},
    )

    bench_resp.raise_for_status()
    return bench_resp.json()


def raw_to_single_row(raw):
    row = {}
    for entry in raw:
        algo = entry["algorithm"]
        if "image" not in row:
            row["image"] = entry["image"]
            row["taille"] = entry["taille (px)"]
            row["pixels"] = entry["pixels"]
            row["max_distance"] = entry["max_distance"]
            row["min_distance"] = entry["min_distance"]
            row["mean_distance"] = entry["mean_distance"]
            row["output_image"] = entry["output_image"]

        if algo == "fast_marching":
            row["temps_fast_marching"] = entry["temps (s)"]
        elif algo == "fast_marching_numba":
            row["temps_fast_marching_numba"] = entry["temps (s)"]

    return row


def compute_mask(image_path, threshold=0.5):
    if not image_path or not os.path.exists(image_path):
        return "Error: no image selected or file not found"

    with open(image_path, "rb") as img:
        files = {"image_file": img}
        data = {"name": "default"}
        resp = requests.post(f"{BASE_URL}/api/images/", files=files, data=data)
    if not resp.ok:
        return f"Error {resp.status_code}: {resp.text}"

    image_id = resp.json().get("id")
    if not image_id:
        return "Error: No image id returned"

    threshold_percent = int(threshold * 100)
    url = f"{BASE_URL}/api/images/{image_id}/preview_mask/?threshold={threshold_percent}"
    mask_resp = requests.get(url)
    if not mask_resp.ok:
        return f"Error {mask_resp.status_code}: {mask_resp.text}"

    return mask_resp.json()

# res = compute_mask('media/inputs/images/img.png')
# print(res)
