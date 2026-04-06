from datetime import datetime, timedelta, timezone
from collections import deque
import heapq
import json


ALL_TRANSPORTS = [1, 2, 3, 4, 5]


class Flight:
    costs = {
        0: 0,
        1: 0.008,
        2: 0.3,
        3: 0.012,
        4: 0.001,
        5: 0.02,
    }

    def __init__(
        self,
        cityA: str,
        cityB: str,
        start_time: datetime,
        arrive_time: datetime,
        id: str,
        transport_type: int,
        company: str | None = None,
    ):
        self.cityA = cityA
        self.cityB = cityB
        self.start_time = start_time
        self.arrive_time = arrive_time
        self.cost = int((arrive_time - start_time).total_seconds()) * Flight.costs.get(transport_type, 0.01)
        self.duration = self.arrive_time - self.start_time
        self.id = id
        self.transport_type = transport_type
        self.company = company

    def __str__(self):
        return "from " + str(self.cityA) + " " + \
            " to " + str(self.cityB) + "    " + \
            " from " + str(self.start_time) + " " + \
            " to " + str(self.arrive_time) + "      " + \
            f"{self.cost:.2f}" + " rubles    " + \
            " bort id " + str(self.id) + " " + \
            " type_transport " + str(self.transport_type) + '\n'

    def check_transport_list(self, transport_list):
        return self.transport_type in transport_list


class Graph:
    def __init__(self, flight_delay=timedelta(0), file_path="flights.json"):
        self.graph = {}
        # 2026-04-06 05:11 (+07): cache city timezones from the loaded schedule
        # so API requests use aware datetimes in the correct local zone.
        self.city_timezones = {}
        self.flight_delay = flight_delay
        self.file_path = file_path
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for name, flight_list in data.items():
            self.graph[name] = []
            for flight in flight_list:
                start_time = datetime.fromisoformat(flight["departure"])
                arrive_time = datetime.fromisoformat(flight["arrival"])
                fl_obj = Flight(
                    cityA=flight["from"],
                    cityB=flight["to"],
                    start_time=start_time,
                    arrive_time=arrive_time,
                    id=flight["number"],
                    transport_type=flight["type"],
                    company=flight.get("company"),
                )
                self.graph[name].append(fl_obj)
                self.city_timezones.setdefault(flight["from"], start_time.tzinfo)
                self.city_timezones.setdefault(flight["to"], arrive_time.tzinfo)

    def __str__(self):
        out = ""
        for name, flight_list in self.graph.items():
            out += name + "\n"
            for flight in flight_list:
                out += "     " + str(flight)
        return out

    def _default_transport_list(self, transport_list):
        if transport_list is None:
            return ALL_TRANSPORTS
        return transport_list

    def _sentinel_flight(self):
        base_time = datetime(1, 1, 1, tzinfo=timezone.utc)
        return Flight("", "", base_time, base_time, "SENTINEL", 0)

    def get_city_timezone(self, city: str):
        return self.city_timezones.get(city, timezone.utc)

    def get_all_routes(self, cityA: str, cityB: str, departure_time: datetime, max_transfers: int = 3, transport_list=None):
        transport_list = self._default_transport_list(transport_list)
        res = []
        q = deque([(cityA, [], departure_time, {cityA})])

        while q:
            curr_city, path, curr_time, visited = q.popleft()

            if curr_city == cityB and path:
                res.append(path)
                continue

            if len(path) > max_transfers:
                continue

            if curr_city not in self.graph:
                continue

            for flight in self.graph[curr_city]:
                if not flight.check_transport_list(transport_list):
                    continue

                if flight.start_time < curr_time + self.flight_delay:
                    continue

                if flight.cityB in visited:
                    continue

                q.append((flight.cityB, path + [flight], flight.arrive_time, visited | {flight.cityB}))

        return res

    def get_min_changes(self, cityA: str, cityB: str, departure_time: datetime, arrivetime=datetime(9999, 2, 1, tzinfo=timezone.utc), transport_list=None):
        transport_list = self._default_transport_list(transport_list)
        changes = {name: float("inf") for name in self.graph.keys()}
        time = {name: datetime(9999, 1, 1, tzinfo=timezone.utc) for name in self.graph.keys()}
        previos_flight = {name: self._sentinel_flight() for name in self.graph.keys()}
        q = deque()

        if cityA not in changes:
            return ['Нет подходящих рейсов😭']

        time[cityA] = departure_time
        changes[cityA] = 0
        q.append(cityA)
        while q:
            curr_city = q.popleft()
            for flight in self.graph.get(curr_city, []):
                if flight.start_time < time[curr_city] + self.flight_delay or not flight.check_transport_list(transport_list):
                    continue

                if time[flight.cityB] > flight.arrive_time and changes[curr_city] + 1 == changes[flight.cityB] and arrivetime > flight.arrive_time:
                    time[flight.cityB] = flight.arrive_time
                    previos_flight[flight.cityB] = flight
                    q.appendleft(flight.cityB)

                # 2026-04-06 05:11 (+07): fixed the deadline check here.
                # We must compare the limit with this flight's arrival, not with stale saved city time.
                if changes[curr_city] + 1 < changes[flight.cityB] and arrivetime > flight.arrive_time:
                    changes[flight.cityB] = changes[curr_city] + 1
                    time[flight.cityB] = flight.arrive_time
                    previos_flight[flight.cityB] = flight
                    q.append(flight.cityB)

        flight_lst = []
        current_city = cityB
        if current_city not in previos_flight:
            return ['Нет подходящих рейсов😭']

        while previos_flight[current_city].id != "SENTINEL":
            flight_lst.append(previos_flight[current_city])
            current_city = previos_flight[current_city].cityA

        flight_lst.reverse()
        if len(flight_lst) == 0:
            flight_lst = ['Нет подходящих рейсов😭']
        return flight_lst

    def get_min_duration(self, cityA: str, cityB: str, departure_time: datetime, arrivetime=datetime(9999, 2, 1, tzinfo=timezone.utc), transport_list=None):
        transport_list = self._default_transport_list(transport_list)
        min_time = {name: datetime(9999, 1, 1, tzinfo=timezone.utc) for name in self.graph.keys()}
        previos_flight = {name: self._sentinel_flight() for name in self.graph.keys()}
        if cityA not in min_time:
            return ['Нет подходящих рейсов😭']

        min_time[cityA] = departure_time
        vertex_set_moment = [(departure_time, cityA)]

        while vertex_set_moment:
            first_moment, curr_city = heapq.heappop(vertex_set_moment)
            if first_moment != min_time[curr_city]:
                continue

            for flight in self.graph.get(curr_city, []):
                if first_moment + self.flight_delay > flight.start_time or not flight.check_transport_list(transport_list):
                    continue
                arr_time = flight.arrive_time

                if min_time[flight.cityB] > arr_time and arrivetime > arr_time:
                    min_time[flight.cityB] = arr_time
                    previos_flight[flight.cityB] = flight
                    heapq.heappush(vertex_set_moment, (arr_time, flight.cityB))

        flight_lst = []
        cur_city = cityB
        if cur_city not in previos_flight:
            return ['Нет подходящих рейсов😭']

        while previos_flight[cur_city].id != "SENTINEL":
            flight_lst.append(previos_flight[cur_city])
            cur_city = previos_flight[cur_city].cityA

        flight_lst.reverse()
        if len(flight_lst) == 0:
            flight_lst = ['Нет подходящих рейсов😭']
        return flight_lst

    def get_min_cost(self, cityA: str, cityB: str, departure_time: datetime, arrivetime=datetime(9999, 2, 1, tzinfo=timezone.utc), min_cost=0, max_cost=1e18, transport_list=None):
        transport_list = self._default_transport_list(transport_list)
        costs = {name: float("inf") for name in self.graph.keys()}
        time = {name: datetime(9999, 1, 1, tzinfo=timezone.utc) for name in self.graph.keys()}
        previos_flight = {name: self._sentinel_flight() for name in self.graph.keys()}
        q = deque()

        if cityA not in costs:
            return ['Нет подходящих рейсов😭']

        time[cityA] = departure_time
        costs[cityA] = 0
        q.append(cityA)
        while q:
            curr_city = q.popleft()
            for flight in self.graph.get(curr_city, []):
                if flight.start_time < time[curr_city] + self.flight_delay or not flight.check_transport_list(transport_list):
                    continue

                next_cost = costs[curr_city] + flight.cost
                if next_cost < min_cost or next_cost > max_cost:
                    continue

                if time[flight.cityB] > flight.arrive_time and next_cost == costs[flight.cityB] and arrivetime > flight.arrive_time:
                    time[flight.cityB] = flight.arrive_time
                    previos_flight[flight.cityB] = flight
                    q.appendleft(flight.cityB)

                if next_cost < costs[flight.cityB] and arrivetime > flight.arrive_time:
                    costs[flight.cityB] = next_cost
                    time[flight.cityB] = flight.arrive_time
                    previos_flight[flight.cityB] = flight
                    q.append(flight.cityB)

        flight_lst = []
        current_city = cityB
        if current_city not in previos_flight:
            return ['Нет подходящих рейсов😭']

        while previos_flight[current_city].id != "SENTINEL":
            flight_lst.append(previos_flight[current_city])
            current_city = previos_flight[current_city].cityA

        flight_lst.reverse()
        if len(flight_lst) == 0:
            flight_lst = ['Нет подходящих рейсов😭']
        return flight_lst

    def get_straight_races(self, cityA: str, cityB: str, departure_time: datetime, transport_list=None):
        transport_list = self._default_transport_list(transport_list)
        if cityA not in self.graph:
            return ['Нет подходящих рейсов😭']

        lst = [
            flight for flight in self.graph[cityA]
            if flight.cityB == cityB
            and flight.check_transport_list(transport_list)
            and flight.start_time >= departure_time
        ]
        if len(lst) == 0:
            lst = ['Нет подходящих рейсов😭']
        return lst

    def get_all_moves(self, cityA, departure_time):
        if cityA not in self.graph:
            return ['Нет подходящих рейсов😭']

        lst = [flight for flight in self.graph[cityA] if flight.start_time.date() == departure_time.date()]
        if len(lst) == 0:
            lst = ['Нет подходящих рейсов😭']
        return lst
