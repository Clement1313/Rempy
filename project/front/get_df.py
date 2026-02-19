import requests
import pandas as pd

BASE_URL = "http://localhost:8000/api"

def create_benchmark(name: str, image_ids: list[int]):
    payload = {"name": name, "image_ids": image_ids}
    resp = requests.post(f"{BASE_URL}/benchmarks/", json=payload)
    resp.raise_for_status()
    return pd.DataFrame.from_dict(resp)