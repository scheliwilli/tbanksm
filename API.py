import ipaddress
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from map.map import ALL_TRANSPORTS, Flight, Graph

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLIGHT_FILE = os.path.join(BASE_DIR, "map", "flights.json")

flight_graph = Graph(flight_delay=timedelta(0), file_path=FLIGHT_FILE)

# 2026-04-06 05:11 (+07): fixed transport code mismatch with flights.json:
# type 3 is bus, type 4 is electrictrain. Previously these two were swapped.
TRANSPORT_LABELS = {
    1: "train",
    2: "plane",
    3: "bus",
    4: "electrictrain",
    5: "ship",
}
TRANSPORT_QUERY_MAP = {
    "train": [1],
    "plane": [2],
    "bus": [3],
    "electrictrain": [4],
    "ship": [5],
    "all": ALL_TRANSPORTS,
}

SUPPORTED_SORTS = {"cost", "duration", "transfers", "departure", "closest_time"}
MAX_RETURNED_ROUTES = 200
MAX_ITINERARY_OPTIONS_PER_LEG = 120


class ItineraryStop(BaseModel):
    city: str
    stay_hours: int = Field(24, ge=0, le=24 * 30)


class ItineraryRequest(BaseModel):
    origin: str
    date: str
    stops: list[ItineraryStop] = Field(default_factory=list)
    transport: list[str] = Field(default_factory=list)
    max_transfers: int = Field(3, ge=0, le=5)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def format_datetime(value: datetime, target_tz=None) -> str:
    if target_tz is not None:
        value = value.astimezone(target_tz)
    return value.strftime("%d.%m.%Y %H:%M")


def get_client_ip(request: Request) -> Optional[str]:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    for header_name in ("x-real-ip", "cf-connecting-ip"):
        value = request.headers.get(header_name)
        if value:
            return value.strip()

    if request.client:
        return request.client.host
    return None


def is_public_ip(value: Optional[str]) -> bool:
    if not value:
        return False

    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False

    return not any(
        (
            address.is_private,
            address.is_loopback,
            address.is_reserved,
            address.is_unspecified,
            address.is_link_local,
            address.is_multicast,
        )
    )


def load_ip_context(ip_address: Optional[str]) -> dict:
    if not is_public_ip(ip_address):
        return {}

    url = f"https://ipapi.co/{ip_address}/json/"
    req = UrlRequest(url, headers={"User-Agent": "t-travel-route-planner/1.0"})
    try:
        with urlopen(req, timeout=2.5) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return {}

    if payload.get("error"):
        return {}

    return {
        "city": payload.get("city") or None,
        "region": payload.get("region") or None,
        "country": payload.get("country_name") or None,
        "timezone": payload.get("timezone") or None,
        "source": "ip",
    }


def safe_zoneinfo(name: Optional[str]):
    if not name:
        return None
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return None


def build_client_context(request: Optional[Request], fallback_city: Optional[str] = None) -> dict:
    browser_timezone = request.headers.get("x-client-timezone") if request else None
    ip_address = get_client_ip(request) if request else None
    ip_context = load_ip_context(ip_address) if request else {}

    timezone_name = browser_timezone or ip_context.get("timezone")
    timezone_source = "browser" if browser_timezone else "ip" if ip_context.get("timezone") else "fallback"
    target_tz = safe_zoneinfo(timezone_name)

    # 2026-04-06 05:11 (+07): times are now converted to the client's local zone.
    # We prefer the browser timezone, then IP geolocation, then the origin city's timezone.
    if target_tz is None and fallback_city:
        target_tz = flight_graph.get_city_timezone(fallback_city)
        timezone_name = timezone_name or str(target_tz)

    if target_tz is None:
        target_tz = timezone.utc
        timezone_name = timezone_name or "UTC"

    return {
        "ip": ip_address,
        "city": ip_context.get("city"),
        "region": ip_context.get("region"),
        "country": ip_context.get("country"),
        "timezone": timezone_name,
        "timezone_source": timezone_source,
        "city_source": ip_context.get("source", "unavailable"),
        "tzinfo": target_tz,
    }


def serialize_client_context(client_context: dict) -> dict:
    return {
        "ip": client_context.get("ip"),
        "city": client_context.get("city"),
        "region": client_context.get("region"),
        "country": client_context.get("country"),
        "timezone": client_context.get("timezone"),
        "timezone_source": client_context.get("timezone_source"),
        "city_source": client_context.get("city_source"),
    }


def parse_transport_codes(transport_value) -> list[int]:
    if transport_value is None or transport_value == "":
        return ALL_TRANSPORTS

    if isinstance(transport_value, str):
        raw_values = [part.strip() for part in transport_value.split(",") if part.strip()]
    else:
        raw_values = [str(part).strip() for part in transport_value if str(part).strip()]

    if not raw_values:
        return ALL_TRANSPORTS

    selected_codes = []
    for raw_value in raw_values:
        codes = TRANSPORT_QUERY_MAP.get(raw_value)
        if codes is None:
            raise HTTPException(400, f"Unsupported transport: {raw_value}")
        for code in codes:
            if code not in selected_codes:
                selected_codes.append(code)

    return selected_codes or ALL_TRANSPORTS


def parse_route_date(date_value: str, city: str) -> datetime:
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            base_date = datetime.strptime(date_value, fmt)
            # 2026-04-06 05:11 (+07): fixed the naive/aware datetime crash by
            # anchoring the request date to the departure city's timezone.
            return base_date.replace(tzinfo=flight_graph.get_city_timezone(city))
        except ValueError:
            continue
    raise HTTPException(400, "Error format")


def total_route_cost(path: list[Flight]) -> float:
    return round(sum(fl.cost for fl in path), 2)


def total_route_duration(path: list[Flight]) -> int:
    return int((path[-1].arrive_time - path[0].start_time).total_seconds() / 60)


def flight_to_segment(fl: Flight, client_context: dict) -> dict:
    target_tz = client_context["tzinfo"]
    return {
        "id": fl.id,
        "carrier": fl.company,
        "from": fl.cityA,
        "to": fl.cityB,
        "departure": format_datetime(fl.start_time, target_tz),
        "arrival": format_datetime(fl.arrive_time, target_tz),
        "departure_iso": fl.start_time.astimezone(target_tz).isoformat(),
        "arrival_iso": fl.arrive_time.astimezone(target_tz).isoformat(),
        "cost": round(fl.cost, 2),
        "transport": TRANSPORT_LABELS.get(fl.transport_type, "unknown"),
        "duration_min": int(fl.duration.total_seconds() / 60),
    }


def route_to_payload(path: list[Flight], client_context: dict) -> dict:
    segments = [flight_to_segment(fl, client_context) for fl in path]
    return {
        "segments": segments,
        "transfers": max(0, len(path) - 1),
        "total_cost": total_route_cost(path),
        "total_duration_min": total_route_duration(path),
        "departure": segments[0]["departure"],
        "arrival": segments[-1]["arrival"],
        "departure_iso": segments[0]["departure_iso"],
        "arrival_iso": segments[-1]["arrival_iso"],
    }


def filter_paths(paths: list[list[Flight]], max_transfers: Optional[int], min_cost: Optional[float], max_cost: Optional[float], min_duration: Optional[int], max_duration: Optional[int]) -> list[list[Flight]]:
    valid_paths = []
    for path in paths:
        transfers = max(0, len(path) - 1)
        if max_transfers is not None and transfers > max_transfers:
            continue

        total_cost = total_route_cost(path)
        if min_cost is not None and total_cost < min_cost:
            continue
        if max_cost is not None and total_cost > max_cost:
            continue

        total_duration_min = total_route_duration(path)
        if min_duration is not None and total_duration_min < min_duration:
            continue
        if max_duration is not None and total_duration_min > max_duration:
            continue

        valid_paths.append(path)
    return valid_paths


def sort_paths(paths: list[list[Flight]], sort_by: Optional[str], sort_order: str, not_before: datetime) -> list[list[Flight]]:
    reverse = sort_order == "desc"
    if sort_by == "cost":
        paths.sort(key=total_route_cost, reverse=reverse)
    elif sort_by == "duration":
        paths.sort(key=total_route_duration, reverse=reverse)
    elif sort_by == "transfers":
        paths.sort(key=lambda p: max(0, len(p) - 1), reverse=reverse)
    elif sort_by == "departure":
        paths.sort(key=lambda p: p[0].start_time, reverse=reverse)
    elif sort_by == "closest_time":
        paths.sort(key=lambda p: abs((p[0].start_time - not_before).total_seconds()), reverse=reverse)
    return paths


def empty_routes_response(origin: str, destination: str, date: str, sort_by: Optional[str], client_context: dict) -> dict:
    return {
        "origin": origin,
        "destination": destination,
        "date": date,
        "sort_by": sort_by or "none",
        "count": 0,
        "total_found": 0,
        "is_truncated": False,
        "routes": [],
        "client_context": serialize_client_context(client_context),
    }


def format_stay_label(total_minutes: int) -> str:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    parts = []
    if hours:
        parts.append(f"{hours} ч")
    if minutes:
        parts.append(f"{minutes} мин")
    if not parts:
        parts.append("0 мин")
    return " ".join(parts)


def prune_itinerary_states(states: list[dict]) -> list[dict]:
    states.sort(key=lambda state: (state["ready_time"], state["total_cost"], state["arrival_time"]))
    pruned = []
    best_cost_so_far = float("inf")
    for state in states:
        if state["total_cost"] < best_cost_so_far:
            pruned.append(state)
            best_cost_so_far = state["total_cost"]
    return pruned


def prune_candidate_paths(paths: list[list[Flight]], limit: Optional[int] = None) -> list[list[Flight]]:
    ranked_paths = sorted(paths, key=lambda path: (path[-1].arrive_time, total_route_cost(path), total_route_duration(path)))
    pruned = []
    best_cost_so_far = float("inf")

    for path in ranked_paths:
        current_cost = total_route_cost(path)
        if current_cost < best_cost_so_far:
            pruned.append(path)
            best_cost_so_far = current_cost
            if limit is not None and len(pruned) >= limit:
                break

    return pruned or ranked_paths[:limit]


def build_single_route_response(
    request: Optional[Request],
    origin: str,
    destination: str,
    date: str,
    sort_by: Optional[str],
    sort_order: str,
    transport,
    max_transfers: Optional[int],
    min_cost: Optional[float],
    max_cost: Optional[float],
    min_duration: Optional[int],
    max_duration: Optional[int],
) -> dict:
    if origin not in flight_graph.graph or destination not in flight_graph.graph:
        raise HTTPException(404, "Not found")
    if origin == destination:
        raise HTTPException(400, "Matches")

    client_context = build_client_context(request, fallback_city=origin)
    not_before = parse_route_date(date, origin)
    transport_list = parse_transport_codes(transport)
    normalized_max_transfers = 3 if max_transfers is None else max_transfers

    paths = flight_graph.get_all_routes(
        origin,
        destination,
        not_before,
        transport_list=transport_list,
        max_transfers=normalized_max_transfers,
    )

    if not paths:
        return empty_routes_response(origin, destination, date, sort_by, client_context)

    valid_paths = filter_paths(paths, max_transfers, min_cost, max_cost, min_duration, max_duration)
    sort_paths(valid_paths, sort_by, sort_order, not_before)

    total_found = len(valid_paths)
    routes = [route_to_payload(path, client_context) for path in valid_paths[:MAX_RETURNED_ROUTES]]
    return {
        "origin": origin,
        "destination": destination,
        "date": date,
        "sort_by": sort_by or "none",
        "count": len(routes),
        "total_found": total_found,
        "is_truncated": total_found > MAX_RETURNED_ROUTES,
        "routes": routes,
        "client_context": serialize_client_context(client_context),
    }


def build_itinerary_response(request: Optional[Request], payload: ItineraryRequest) -> dict:
    if payload.origin not in flight_graph.graph:
        raise HTTPException(404, "Not found")
    if not payload.stops:
        raise HTTPException(400, "Add at least one city")
    if len(payload.stops) > 5:
        raise HTTPException(400, "Too many cities in itinerary")

    previous_city = payload.origin
    for stop in payload.stops:
        if stop.city not in flight_graph.graph:
            raise HTTPException(404, f"Unknown city: {stop.city}")
        if stop.city == previous_city:
            raise HTTPException(400, "Уберите одинаковые соседние города в маршруте")
        previous_city = stop.city

    client_context = build_client_context(request, fallback_city=payload.origin)
    departure_time = parse_route_date(payload.date, payload.origin)
    transport_list = parse_transport_codes(payload.transport)

    current_states = [{
        "current_city": payload.origin,
        "ready_time": departure_time,
        "arrival_time": departure_time,
        "total_cost": 0.0,
        "paths": [],
        "stays": [],
    }]

    for index, stop in enumerate(payload.stops):
        next_states = []
        stay_delta = timedelta(hours=stop.stay_hours)

        for state in current_states:
            routes = flight_graph.get_all_routes(
                state["current_city"],
                stop.city,
                state["ready_time"],
                max_transfers=payload.max_transfers,
                transport_list=transport_list,
            )
            routes = prune_candidate_paths(routes, limit=MAX_ITINERARY_OPTIONS_PER_LEG)

            for path in routes:
                if not path:
                    continue
                arrival_time = path[-1].arrive_time
                next_states.append({
                    "current_city": stop.city,
                    "ready_time": arrival_time + stay_delta,
                    "arrival_time": arrival_time,
                    "total_cost": round(state["total_cost"] + total_route_cost(path), 2),
                    "paths": state["paths"] + [path],
                    "stays": state["stays"] + [stop.stay_hours * 60],
                })

        if not next_states:
            failed_from = current_states[0]["current_city"] if current_states else payload.origin
            return {
                "found": False,
                "origin": payload.origin,
                "date": payload.date,
                "message": f"Не удалось построить маршрут {failed_from} -> {stop.city}",
                "failed_leg": {
                    "from": failed_from,
                    "to": stop.city,
                },
                "client_context": serialize_client_context(client_context),
                "legs": [],
                "stops": [stop.model_dump() for stop in payload.stops],
            }

        current_states = prune_itinerary_states(next_states)

    best_state = min(current_states, key=lambda state: (state["total_cost"], state["arrival_time"]))
    legs = []
    route_paths = best_state["paths"]

    for stop, path in zip(payload.stops, best_state["paths"]):
        leg_payload = route_to_payload(path, client_context)
        leg_payload.update({
            "origin": path[0].cityA,
            "destination": path[-1].cityB,
            "stay_hours_after_arrival": stop.stay_hours,
            "stay_label_after_arrival": format_stay_label(stop.stay_hours * 60),
        })
        legs.append(leg_payload)

    if route_paths:
        overall_finish = route_paths[-1][-1].arrive_time
        total_duration_min = int((overall_finish - departure_time).total_seconds() / 60)
    else:
        total_duration_min = 0

    return {
        "found": True,
        "origin": payload.origin,
        "date": payload.date,
        "legs": legs,
        "stops": [stop.model_dump() for stop in payload.stops],
        "total_cost": round(best_state["total_cost"], 2),
        "total_duration_min": total_duration_min,
        "total_transfers": sum(max(0, len(path) - 1) for path in route_paths),
        "client_context": serialize_client_context(client_context),
    }


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/cities")
def get_cities():
    return {"cities": sorted(flight_graph.graph.keys())}


@app.get("/client-context")
def get_client_context(request: Request):
    return serialize_client_context(build_client_context(request))


@app.get("/routes")
def search_routes(
    request: Request,
    origin: str = Query(...),
    destination: str = Query(...),
    date: str = Query(...),
    sort_by: Optional[Literal["cost", "duration", "transfers", "departure", "closest_time"]] = Query(None),
    sort_order: Literal["asc", "desc"] = Query("asc"),
    transport: Optional[str] = Query(None),
    max_transfers: Optional[int] = Query(None),
    min_cost: Optional[float] = Query(None),
    max_cost: Optional[float] = Query(None),
    min_duration: Optional[int] = Query(None),
    max_duration: Optional[int] = Query(None),
):
    return build_single_route_response(
        request=request,
        origin=origin,
        destination=destination,
        date=date,
        sort_by=sort_by,
        sort_order=sort_order,
        transport=transport,
        max_transfers=max_transfers,
        min_cost=min_cost,
        max_cost=max_cost,
        min_duration=min_duration,
        max_duration=max_duration,
    )


@app.post("/itinerary")
def build_itinerary(request: Request, payload: ItineraryRequest):
    return build_itinerary_response(request, payload)


@app.get("/flights/{city}")
def get_flights_from(request: Request, city: str):
    if city not in flight_graph.graph:
        raise HTTPException(404, "Not found")

    client_context = build_client_context(request, fallback_city=city)
    return {
        "city": city,
        "count": len(flight_graph.graph[city]),
        "client_context": serialize_client_context(client_context),
        "flights": [flight_to_segment(fl, client_context) for fl in flight_graph.graph[city]],
    }
