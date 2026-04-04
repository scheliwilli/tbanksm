from datetime import datetime
from datetime import timedelta
from enum import Enum
from collections import deque
import heapq
import json


class TransportType(Enum):
    TRAIN = 1
    PLANE = 2
    ELECTRICTRAIN = 3



class Flight:
    def __init__(self,
                 cityA: str,
                 cityB: str,
                 start_time: datetime,
                 arrive_time: datetime,
                 cost: int,
                 id: int,
                 transport_type: TransportType):
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
                    flight[0],
                    flight[1],
                    datetime.strptime(flight[2], "%d.%m.%Y %H:%M"),
                    datetime.strptime(flight[3], "%d.%m.%Y %H:%M"),
                    int(flight[4]),
                    int(flight[5]),
                    int(flight[6])
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
    

    def get_min_changes(self, cityA: str, cityB: str, departure_time, transport_list = [1, 2, 3]):
        changes = {name: float("inf") for name, flights in self.graph.items()}
        time = {name: datetime(9999, 1, 1) for name, flights in self.graph.items()}
        previos_flight = {name: Flight("", "", 1, 1, 1, -1, 1) for name, flights in self.graph.items()}
        q = deque()

        time[cityA] = departure_time
        changes[cityA] = 0
        q.append(cityA)
        while (q):
            curr_city = q.popleft()
            for flight in self.graph[cityA]:
                if (flight.start_time < time[curr_city] + self.flight_delay) or not flight.check_transport_list(transport_list):  # Проверка успеем ли на рейс
                    continue

                if (time[flight.cityB] > flight.arrive_time and changes[curr_city] + 1 == changes[flight.cityB]):
                    time[flight.cityB] = flight.arrive_time
                    previos_flight[flight.cityB] = flight
                    q.appendleft(flight.cityB)

                if changes[curr_city] + 1 < changes[flight.cityB]:
                    changes[flight.cityB] = changes[curr_city] + 1
                    previos_flight[flight.cityB] = flight
                    q.append(flight.cityB)

        flight_lst = []
        current_city = cityB
        while previos_flight[current_city].id != -1:
            flight_lst.append(previos_flight[current_city])
            current_city = previos_flight[current_city].cityA

        flight_lst.reverse()
        if len(flight_lst) == 0:
            flight_lst = ['Нет подходящих рейсов😭']
        return flight_lst

    def get_min_duration(self, cityA: str, cityB: str, departure_time: datetime, transport_list=[1, 2, 3]):

        min_time = {name: datetime(9999, 1, 1) for name, flights in self.graph.items()}
        previos_flight = {name: Flight("", "", 1, 1, 1, -1, 1) for name, flights in self.graph.items()}
        min_time[cityA] = departure_time
        vertex_set_moment = [(departure_time, cityA)]

        while vertex_set_moment:
            first_moment, cityA = heapq.heappop(vertex_set_moment)

            for flight in self.graph[cityA]:
                if (first_moment + self.flight_delay > flight.start_time) or not flight.check_transport_list(transport_list):
                    continue
                time = flight.arrive_time

                if min_time[flight.cityB] > time:
                    min_time[flight.cityB] = time
                    previos_flight[flight.cityB] = flight
                    heapq.heappush(vertex_set_moment, (time, flight.cityB))


        flight_lst = []
        cur_city = cityB
        while previos_flight[cur_city].id != -1:
            flight_lst.append(previos_flight[cur_city])
            cur_city = previos_flight[cur_city].cityA

        flight_lst.reverse()
        if len(flight_lst) == 0:
            flight_lst = ['Нет подходящих рейсов😭']
        return flight_lst

    def get_min_cost(self, cityA: str, cityB: str, departure_time: datetime, min_cost = 0, max_cost = 1e18, transport_list=[1, 2, 3]):
        costs = {name: float("inf") for name, flights in self.graph.items()}
        time = {name: datetime(9999, 1, 1) for name, flights in self.graph.items()}
        previos_flight = {name: Flight("", "", 1, 1, 1, -1, 1) for name, flights in self.graph.items()}
        q = deque()

        time[cityA] = departure_time
        costs[cityA] = 0
        q.append(cityA)
        while (q):
            curr_city = q.popleft()
            for flight in self.graph[cityA]:
                if (flight.start_time < time[curr_city] + self.flight_delay) or not flight.check_transport_list(transport_list):  # Проверка успеем ли на рейс
                    continue

                if (time[flight.cityB] > flight.arrive_time and costs[curr_city] + flight.cost == costs[flight.cityB]):
                    time[flight.cityB] = flight.arrive_time
                    previos_flight[flight.cityB] = flight
                    q.appendleft(flight.cityB)

                if costs[curr_city] + flight.cost < costs[flight.cityB]:
                    costs[flight.cityB] = costs[curr_city] + flight.cost
                    previos_flight[flight.cityB] = flight
                    q.append(flight.cityB)

        flight_lst = []
        current_city = cityB
        while previos_flight[current_city].id != -1:
            flight_lst.append(previos_flight[current_city])
            current_city = previos_flight[current_city].cityA

        flight_lst.reverse()
        if len(flight_lst) == 0:
            flight_lst = ['Нет подходящих рейсов😭']
        return flight_lst
    def get_straight_races(self, cityA: str, cityB: str, departure_time: datetime, transport_list=[1, 2, 3]):
        lst = [flight for flight in self.graph[cityA]
                if flight.cityB == cityB
                and flight.check_transport_list(transport_list)
                and flight.start_time >= departure_time]
        if len(lst) == 0:
            lst = ['Нет подходящих рейсов😭']
        return lst