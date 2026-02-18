import requests
import pandas as pd

BASE_URL = "http://localhost:8000/api"

def run_and_display(image_ids: list[int], benchmark_name: str = "test"):
    response = requests.post(f"{BASE_URL}/benchmarks/", json={
        "name": benchmark_name,
        "image_ids": image_ids
    })
    data = response.json()

    if response.status_code != 201:
        print("Erreur:", data)
        return

    rows = []
    for result in data["results"]:
        image_name = result["image_name"]
        metrics    = result["metrics"]
        rows.append({
            "image":         image_name,
            "taille (px)":   f"{metrics.get('image_width', '?')}x{metrics.get('image_height', '?')}",
            "temps algo1 (s)" if result["algorithm"] == "fast_marching" else "temps algo2 (s)": round(result["execution_time"], 4),
        })

    results = data["results"]
    image_names = list({r["image_name"] for r in results})

    table = {}
    for img in image_names:
        img_results = [r for r in results if r["image_name"] == img]
        metrics = img_results[0]["metrics"]
        row = {
            "taille (px)": f"{metrics.get('image_width', '?')}x{metrics.get('image_height', '?')}",
        }
        for r in img_results:
            col = "temps algo1 (s)" if r["algorithm"] == "fast_marching" else "temps algo2 (s)"
            row[col] = round(r["execution_time"], 4)
        table[img] = row

    df = pd.DataFrame.from_dict(table, orient="index")
    df.index.name = "image"

    print(f"\nBenchmark '{data['name']}' — status: {data['status']}\n")
    print(df.to_string())
    print()

if __name__ == "__main__":
    with open(r"C:\Users\Utilisateur\Desktop\ING2\Python\TP1\TP1\TP1\data\img.png",  "rb") as img, \
         open(r"C:\Users\Utilisateur\Desktop\ING2\Python\TP1\TP1\TP1\data\mask.png", "rb") as mask:

        upload = requests.post(f"{BASE_URL}/images/", files={
            "image_file": img,
            "mask_file":  mask,
        }, data={"name": "img1"})

    image_id = upload.json()["id"]
    print(f"Image uploadée → id={image_id}")

    run_and_display([image_id], benchmark_name="test_pandas")