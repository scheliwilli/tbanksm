import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from map.map import Graph, Flight

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLIGHT_FILE = os.path.join(BASE_DIR, "map", "flights.json")

flight_graph = Graph(flight_delay=timedelta(0), file_path=FLIGHT_FILE)

TRANSPORT_LABELS = {1: "train", 2: "plane", 3: "electrictrain", 4: "bus", 5: "ship"}

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

@app.get("/routes")
def search_routes(
    origin: str = Query(...),
    destination: str = Query(...),
    date: str = Query(...),
    sort_by: str = Query("cost", enum=["cost", "duration", "transfers"]),
):
    try:
        not_before = datetime.strptime(date, "%d.%m.%Y")
    except ValueError:
        raise HTTPException(400, "Error format")

    if origin not in flight_graph.graph or destination not in flight_graph.graph:
        raise HTTPException(404, "Not found")
    if origin == destination:
        raise HTTPException(400, "Matches")

    if sort_by == "cost":
        path = flight_graph.get_min_cost(origin, destination, not_before)
    elif sort_by == "duration":
        path = flight_graph.get_min_duration(origin, destination, not_before)
    elif sort_by == "transfers":
        path = flight_graph.get_min_changes(origin, destination, not_before)
    else:
        path = flight_graph.get_min_cost(origin, destination, not_before)

    if not path:
        return {
            "origin": origin,
            "destination": destination,
            "date": date,
            "sort_by": sort_by,
            "count": 0,
            "routes": []
        }

    segments = [flight_to_segment(fl) for fl in path]
    total_cost = sum(fl.cost for fl in path)
    total_duration_min = int((path[-1].arrive_time - path[0].start_time).total_seconds() / 60)

    route_info = {
        "segments": segments,
        "transfers": max(0, len(path) - 1),
        "total_cost": total_cost,
        "total_duration_min": total_duration_min,
        "departure": segments[0]["departure"],
        "arrival": segments[-1]["arrival"],
    }

    return {
        "origin": origin,
        "destination": destination,
        "date": date,
        "sort_by": sort_by,
        "count": 1,
        "routes": [route_info],
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
