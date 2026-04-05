import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from map.map import Graph, Flight

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLIGHT_FILE = os.path.join(BASE_DIR, "map", "flights.json")

flight_graph = Graph(flight_delay=timedelta(0), file_path=FLIGHT_FILE)

TRANSPORT_LABELS = {1: "train", 2: "plane", 3: "electrictrain"}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def flight_to_segment(fl: Flight) -> dict:
    return {
        "from": fl.cityA,
        "to": fl.cityB,
        "departure": fl.start_time.strftime("%d.%m.%Y %H:%M"),
        "arrival": fl.arrive_time.strftime("%d.%m.%Y %H:%M"),
        "cost": fl.cost,
        "transport": TRANSPORT_LABELS.get(fl.transport_type, "unknown"),
        "duration_min": int(fl.duration.total_seconds() / 60),
    }

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/cities")
def get_cities():
    return {"cities": list(flight_graph.graph.keys())}

@app.get("/routes")
def search_routes(
    origin: str = Query(...),
    destination: str = Query(...),
    date: str = Query(...),
    sort_by: Optional[str] = Query(None, enum=["cost", "duration", "transfers"]),
    transport: Optional[str] = Query(None),
    max_transfers: Optional[int] = Query(None),
    min_cost: Optional[int] = Query(None),
    max_cost: Optional[int] = Query(None),
    min_duration: Optional[int] = Query(None),
    max_duration: Optional[int] = Query(None),
):
    try:
        not_before = datetime.strptime(date, "%d.%m.%Y")
    except ValueError:
        raise HTTPException(400, "Error format")

    if origin not in flight_graph.graph or destination not in flight_graph.graph:
        raise HTTPException(404, "Not found")
    if origin == destination:
        raise HTTPException(400, "Matches")
        
    transport_list = [1, 2, 3]
    if transport == "train":
        transport_list = [1]
    elif transport == "plane":
        transport_list = [2]

    paths = flight_graph.get_all_routes(origin, destination, not_before, transport_list=transport_list)

    if not paths:
        return {
            "origin": origin,
            "destination": destination,
            "date": date,
            "sort_by": sort_by or "none",
            "count": 0,
            "routes": []
        }

    valid_paths = []
    for path in paths:
        transfers = max(0, len(path) - 1)
        if max_transfers is not None and transfers > max_transfers:
            continue
            
        total_cost = sum(fl.cost for fl in path)
        if min_cost is not None and total_cost < min_cost:
            continue
        if max_cost is not None and total_cost > max_cost:
            continue

        total_duration_min = int((path[-1].arrive_time - path[0].start_time).total_seconds() / 60)
        if min_duration is not None and total_duration_min < min_duration:
            continue
        if max_duration is not None and total_duration_min > max_duration:
            continue
            
        valid_paths.append(path)

    if sort_by == "cost":
        valid_paths.sort(key=lambda p: sum(fl.cost for fl in p))
    elif sort_by == "duration":
        valid_paths.sort(key=lambda p: (p[-1].arrive_time - p[0].start_time).total_seconds())
    elif sort_by == "transfers":
        valid_paths.sort(key=lambda p: len(p))

    routes = []
    for path in valid_paths:
        segments = [flight_to_segment(fl) for fl in path]
        routes.append({
            "segments": segments,
            "transfers": max(0, len(path) - 1),
            "total_cost": sum(fl.cost for fl in path),
            "total_duration_min": int((path[-1].arrive_time - path[0].start_time).total_seconds() / 60),
            "departure": segments[0]["departure"],
            "arrival": segments[-1]["arrival"],
        })

    return {
        "origin": origin,
        "destination": destination,
        "date": date,
        "sort_by": sort_by or "none",
        "count": len(routes),
        "routes": routes,
    }

@app.get("/flights/{city}")
def get_flights_from(city: str):
    if city not in flight_graph.graph:
        raise HTTPException(404, "Not found")
    return {
        "city": city,
        "count": len(flight_graph.graph[city]),
        "flights": [flight_to_segment(fl) for fl in flight_graph.graph[city]],
    }
