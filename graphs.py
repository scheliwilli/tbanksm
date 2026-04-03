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


class parametres(Enum):
    COST = 1
    CHANGE = 2


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


class Graph:
    def __init__(self, flight_delay=timedelta(0)):
        self.graph = {}
        self.flight_delay = flight_delay
        #   Загрузка полётов из файла
        # Открываем файл для чтения
        with open("flight.json", "r", encoding="utf-8") as f:
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
    

    def get_min_changes(self, cityA: str, cityB: str, start_time):
        changes = {name: float("inf") for name, flights in self.graph.items()}
        time = {name: datetime(9999, 1, 1) for name, flights in self.graph.items()}
        previos_flight = {name: Flight("", "", 1, 1, 1, -1, 1) for name, flights in self.graph.items()}
        q = deque()

        time[cityA] = start_time
        changes[cityA] = 0
        q.append(cityA)
        while (q):
            curr_city = q.popleft()
            for flight in self.graph[cityA]:
                if flight.start_time < time[curr_city] + self.flight_delay:  # Проверка успеем ли на рейс
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
        return flight_lst

    def get_min_duration(self, cityA: str, cityB: str, departure_time: datetime):

        mn_time = {name: float("inf") for name, flights in self.graph.items}
        previos_flight = {name: Flight("", "", 1, 1, 1, -1, 1) for name, flights in self.graph.items}
        mn_time[cityA] = departure_time
        vertex_set_moment = [(departure_time, cityA)]

        while vertex_set_moment:
            tm, cityA = heapq.heappop(vertex_set_moment)

            for flight in self.graph[cityA]:
                if tm + self.flight_delay > flight.start:
                    continue
                time = flight.end

                if mn_time[flight.cityB] > time:
                    mn_time[flight.cityB] = time
                    previos_flight[flight.cityB] = flight
                    heapq.heappush(vertex_set_moment, (time, flight.cityB))


        flight_lst = []
        cur_city = cityB
        while previos_flight[cur_city].id != -1:
            flight_lst.append(previos_flight[cur_city])
            cur_city = previos_flight[cur_city].cityA

        flight_lst.reverse()
        return flight_lst



map = Graph()
# print(map)
date = datetime.strptime("01.01.2020 00:00", "%d.%m.%Y %H:%M")
lst = map.get_min_changes("Moscow", "Vladivostok", date)
# for name, flight_list in graph.items():
for i in lst:
    print(i)