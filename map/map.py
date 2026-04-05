from datetime import datetime, timezone, timedelta
from collections import deque
import heapq
import json


class Flight:
    def __init__(self,
                 cityA: str,
                 cityB: str,
                 start_time: datetime,
                 arrive_time: datetime,
                 cost: int,
                 id: str,
                 transport_type: int):
        self.cityA = cityA
        self.cityB = cityB
        self.start_time = start_time
        self.arrive_time = arrive_time
        self.cost = cost
        self.duration = self.arrive_time - self.start_time
        self.id = id
        self.transport_type = transport_type

    def __str__(self):
        return "from " + str(self.cityA) + " " + \
            " to " + str(self.cityB) + "    " + \
            " from " + str(self.start_time) + " " + \
            " to " + str(self.arrive_time) + "      " + \
            str(self.cost) + " rubles    " + \
            " bort id " + str(self.id) + " " + \
            " type_transport " + str(self.transport_type) + '\n'
    
    def check_transport_list(self, transport_list):
        return (self.transport_type in transport_list)


class Graph:
    def __init__(self, flight_delay=timedelta(0), file_path="flights.json"):
        self.graph = {}
        self.flight_delay = flight_delay
        self.file_path = file_path
        #   Загрузка полётов из файла
        # Открываем файл для чтения
        with open(file_path, "r", encoding="utf-8") as f:
            # Загружаем данные из файла в переменную
            data = json.load(f)

        #   Сохраняем json  в граф
        for name, flight_list in data.items():
            self.graph[name] = []
            for flight in flight_list:
                flight = Flight(
                    cityA=flight["from"],
                    cityB=flight["to"],
                    start_time=datetime.fromisoformat(flight["departure"]),
                    arrive_time=datetime.fromisoformat(flight["arrival"]),
                    cost=0,
                    id=flight["number"],
                    transport_type=flight["type"]
                )
                self.graph[name].append(flight)


    def __str__ (self):
        out = ""
        for name, flight_list in self.graph.items():
            out += name + "\n"
            for flight in flight_list:
                str_flight = "     " + str(flight)
                out += str_flight
        return out
    

    def get_min_changes(self, cityA: str, cityB: str, departure_time, transport_list=[1, 2, 3]):
        visited = {name: {} for name in self.graph.keys()}
        q = []
        push_count = 0
        heapq.heappush(q, (0, departure_time.timestamp(), push_count, cityA, []))
        push_count += 1
        visited[cityA][0] = departure_time

        while q:
            changes, arr_ts, _, curr_city, path = heapq.heappop(q)
            arr_time = datetime.fromtimestamp(arr_ts)

            if curr_city == cityB:
                return path

            for flight in self.graph.get(curr_city, []):
                if not flight.check_transport_list(transport_list):
                    continue
                if flight.start_time < arr_time + self.flight_delay:
                    continue
                if curr_city == cityA and flight.start_time.date() != departure_time.date():
                    continue
                if curr_city != cityA and flight.start_time > arr_time + self.flight_delay + timedelta(hours=48):
                    continue

                new_changes = changes + 1
                new_arr_time = flight.arrive_time
                new_city = flight.cityB

                dom = False
                for c, t in visited.get(new_city, {}).items():
                    if c <= new_changes and t <= new_arr_time:
                        dom = True
                        break

                if not dom:
                    to_keep = {}
                    for c, t in visited.get(new_city, {}).items():
                        if not (new_changes <= c and new_arr_time <= t):
                            to_keep[c] = t
                    to_keep[new_changes] = new_arr_time
                    visited[new_city] = to_keep

                    new_path = path + [flight]
                    heapq.heappush(q, (new_changes, new_arr_time.timestamp(), push_count, new_city, new_path))
                    push_count += 1

        return []

    def get_min_duration(self, cityA: str, cityB: str, departure_time: datetime, transport_list=[1, 2, 3]):
        visited = {name: datetime(9999, 1, 1) for name in self.graph.keys()}
        q = []
        push_count = 0
        heapq.heappush(q, (departure_time.timestamp(), push_count, cityA, []))
        push_count += 1
        visited[cityA] = departure_time

        while q:
            arr_ts, _, curr_city, path = heapq.heappop(q)
            arr_time = datetime.fromtimestamp(arr_ts)

            if curr_city == cityB:
                return path

            if arr_time > visited.get(curr_city, datetime(9999, 1, 1)):
                continue

            for flight in self.graph.get(curr_city, []):
                if not flight.check_transport_list(transport_list):
                    continue
                if flight.start_time < arr_time + self.flight_delay:
                    continue
                if curr_city == cityA and flight.start_time.date() != departure_time.date():
                    continue
                if curr_city != cityA and flight.start_time > arr_time + self.flight_delay + timedelta(hours=48):
                    continue

                new_arr_time = flight.arrive_time
                new_city = flight.cityB

                if new_arr_time < visited.get(new_city, datetime(9999, 1, 1)):
                    visited[new_city] = new_arr_time
                    new_path = path + [flight]
                    heapq.heappush(q, (new_arr_time.timestamp(), push_count, new_city, new_path))
                    push_count += 1

        return []

    def get_min_cost(self, cityA: str, cityB: str, departure_time: datetime, min_cost=0, max_cost=1e18, transport_list=[1, 2, 3]):
        visited = {name: [] for name in self.graph.keys()}
        q = []
        push_count = 0
        heapq.heappush(q, (0, departure_time.timestamp(), push_count, cityA, []))
        push_count += 1
        visited[cityA].append((0, departure_time))

        while q:
            cost, arr_ts, _, curr_city, path = heapq.heappop(q)
            arr_time = datetime.fromtimestamp(arr_ts)

            if curr_city == cityB:
                return path

            for flight in self.graph.get(curr_city, []):
                if not flight.check_transport_list(transport_list):
                    continue
                if flight.start_time < arr_time + self.flight_delay:
                    continue
                if curr_city == cityA and flight.start_time.date() != departure_time.date():
                    continue
                if curr_city != cityA and flight.start_time > arr_time + self.flight_delay + timedelta(hours=48):
                    continue

                new_cost = cost + flight.cost
                new_arr_time = flight.arrive_time
                new_city = flight.cityB

                dom = False
                for c, t in visited.get(new_city, []):
                    if c <= new_cost and t <= new_arr_time:
                        dom = True
                        break

                if not dom:
                    to_keep = []
                    for c, t in visited.get(new_city, []):
                        if not (new_cost <= c and new_arr_time <= t):
                            to_keep.append((c, t))
                    to_keep.append((new_cost, new_arr_time))
                    visited[new_city] = to_keep

                    new_path = path + [flight]
                    heapq.heappush(q, (new_cost, new_arr_time.timestamp(), push_count, new_city, new_path))
                    push_count += 1

        return []
   
    def get_all_routes(self, cityA: str, cityB: str, departure_time: datetime, transport_list=[1, 2, 3], max_transfers=3):
        q = [(cityA, [])]
        valid_paths = []

        while q:
            curr_city, path = q.pop(0)

            if curr_city == cityB:
                valid_paths.append(path)
                continue

            if len(path) > max_transfers:
                continue

            arr_time = path[-1].arrive_time if path else departure_time

            for flight in self.graph.get(curr_city, []):
                if not flight.check_transport_list(transport_list):
                    continue
                if path and flight.start_time < arr_time + self.flight_delay:
                    continue
                if not path and flight.start_time.date() != departure_time.date():
                    continue
                if path and flight.start_time > arr_time + self.flight_delay + timedelta(hours=48):
                    continue

                # предотвращение циклов
                visited_cities = [f.cityA for f in path] + [f.cityB for f in path]
                if flight.cityB in visited_cities and flight.cityB != cityB:
                    continue

                q.append((flight.cityB, path + [flight]))

        return valid_paths
