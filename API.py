import json
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLIGHT_FILE = os.path.join(BASE_DIR, "flight.json")

DATE_FMT = "%d.%m.%Y %H:%M"
TRANSPORT_LABELS = {1: "train", 2: "plane", 3: "electrictrain"}

app = FastAPI(title="T-Travel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_graph() -> dict[str, list[dict]]:
    with open(FLIGHT_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    graph: dict[str, list[dict]] = {}

    for _, flights in raw.items():
        for fl in flights:
            city_from  = fl[0]
            city_to    = fl[1]
            departure  = datetime.strptime(fl[2], DATE_FMT)
            arrival    = datetime.strptime(fl[3], DATE_FMT)
            cost       = int(fl[4])
            transport  = TRANSPORT_LABELS.get(int(fl[6]), "unknown")
            duration   = int((arrival - departure).total_seconds() / 60)

            graph.setdefault(city_from, []).append({
                "from":         city_from,
                "to":           city_to,
                "departure":    departure,
                "arrival":      arrival,
                "cost":         cost,
                "transport":    transport,
                "duration_min": duration,
            })

    return graph


GRAPH = load_graph()


def get_all_cities(graph: dict) -> set[str]:
    cities = set(graph.keys())
    for flights in graph.values():
        for fl in flights:
            cities.add(fl["to"])
    return cities


def serialize_segment(seg: dict) -> dict:
    return {
        "from":         seg["from"],
        "to":           seg["to"],
        "departure":    seg["departure"].strftime(DATE_FMT),
        "arrival":      seg["arrival"].strftime(DATE_FMT),
        "cost":         seg["cost"],
        "transport":    seg["transport"],
        "duration_min": seg["duration_min"],
    }


def find_routes(
    origin: str,
    destination: str,
    not_before: datetime,
    transport_filter: Optional[str],
    max_transfers: int,
) -> list[dict]:
    results: list[dict] = []

    def dfs(city: str, available_from: datetime, path: list[dict], visited: set[str]):
        if len(path) > max_transfers + 1:
            return

        if city == destination and path:
            results.append({
                "segments":          [serialize_segment(s) for s in path],
                "transfers":         len(path) - 1,
                "total_cost":        sum(s["cost"] for s in path),
                "total_duration_min": int(
                    (path[-1]["arrival"] - path[0]["departure"]).total_seconds() / 60
                ),
                "departure":         path[0]["departure"].strftime(DATE_FMT),
                "arrival":           path[-1]["arrival"].strftime(DATE_FMT),
            })
            return

        for flight in GRAPH.get(city, []):
            if transport_filter and flight["transport"] != transport_filter:
                continue
            if flight["departure"] < available_from:
                continue
            if flight["to"] in visited:
                continue

            visited.add(flight["to"])
            path.append(flight)
            dfs(flight["to"], flight["arrival"], path, visited)
            path.pop()
            visited.discard(flight["to"])

    dfs(origin, not_before, [], {origin})
    return results


SORT_KEYS = {
    "cost":      lambda r: r["total_cost"],
    "duration":  lambda r: r["total_duration_min"],
    "transfers": lambda r: r["transfers"],
    "departure": lambda r: r["departure"],
}


@app.get("/")
def root():
    return {"status": "ok", "service": "T-Travel API"}


@app.get("/routes")
def search_routes(
    origin: str = Query(...),
    destination: str = Query(...),
    date: str = Query(..., description="Дата отправления DD.MM.YYYY"),
    sort_by: str = Query("cost", enum=["cost", "duration", "transfers", "departure"]),
    transport: Optional[str] = Query(None, enum=["plane", "train", "electrictrain"]),
    max_transfers: int = Query(3, ge=0, le=5),
):
    try:
        not_before = datetime.strptime(date, "%d.%m.%Y")
    except ValueError:
        raise HTTPException(400, "Неверный формат даты. Используйте DD.MM.YYYY")

    cities = get_all_cities(GRAPH)

    if origin not in cities:
        raise HTTPException(404, f"Город '{origin}' не найден")
    if destination not in cities:
        raise HTTPException(404, f"Город '{destination}' не найден")
    if origin == destination:
        raise HTTPException(400, "Город отправления и назначения совпадают")

    routes = find_routes(origin, destination, not_before, transport, max_transfers)
    routes.sort(key=SORT_KEYS[sort_by])

    return {
        "origin":           origin,
        "destination":      destination,
        "date":             date,
        "sort_by":          sort_by,
        "transport_filter": transport,
        "count":            len(routes),
        "routes":           routes,
    }


@app.get("/flights/{city}")
def get_flights_from(city: str):
    if city not in GRAPH:
        raise HTTPException(404, f"Город '{city}' не найден или не является городом отправления")
    return {
        "city":    city,
        "count":   len(GRAPH[city]),
        "flights": [serialize_segment(fl) for fl in GRAPH[city]],
    }
