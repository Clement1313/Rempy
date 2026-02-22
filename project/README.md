# Fast Marching Method Benchmark

A benchmarking project comparing two implementations of the Fast Marching Method : one classic and one accelerated with **Numba**. 


## Getting Started

Clone the repository:

```bash
git clone git@github.com:Clement1313/Rempy.git
cd project
```

Run Docker compose:

```bash
docker compose up --build

docker compose exec back python manage.py makemigrations benchmarks

docker compose exec back python manage.py migrate 

```

Application runs on `http://0.0.0.0:8050/`