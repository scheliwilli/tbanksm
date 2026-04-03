from datetime import datetime
from enum import Enum
from collections import deque
import json

class TransportType (Enum):
    TRAIN = 1
    PLANE = 2
    ELECTRICTRAIN = 3

class parametres (Enum):
    COST = 1
    CHANGE = 2

class Flight:
    def __init__ (self, 
                  cityB : str, 
                  start_time : datetime, 
                  arrive_time : datetime, 
                  cost : int,
                  id: int,
                  transport_type: TransportType):
        self.cityB = cityB
        self.start_time = start_time
        self.arrive_time = arrive_time
        self.cost = cost
        self.duration = self.arrive_time - self.start_time
        self.id = id
        self.transport_type = transport_type

    def  __str__(self):
        return str(self.cityB) + \
                str(self.start_time) + \
                str(self.arrive_time) + \
                str(self.cost) + \
                str(self.duration) + \
                str(self.id) + \
                str(self.transport_type)



class Graph:
    def __init__(self, flight_delay=0):
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
                    datetime.strptime(flight[1], "%d.%m.%Y %H:%M"),
                    datetime.strptime(flight[2], "%d.%m.%Y %H:%M"),
                    int(flight[3]),
                    int(flight[4]),
                    int(flight[5])
                )
                self.graph[name].append(flight)

    def bfs (self, cityA:str, cityB:str, start_time):
        changes = {name: float("inf") for name, flights in self.graph.items}
        time = {name: float("inf") for name, flights in self.graph.items}
        q = deque()

        time[cityA] = start_time
        changes[cityA] = 0
        q.append(cityA)
        while (q):
            curr_city = q.popleft()
            for flight in self.graph[cityA]:
                if flight.start_time < time[curr_city] + self.flight_delay:        # Проверка успеем ли на рейс
                    continue

                if changes[curr_city.id] + 1 < changes[flight.cityB.id]:
                    changes[flight.cityB.id] = changes[curr_city.id] + 1
                    if (time[flight.cityB] > flight.end_time):
                        time[flight.cityB.id] = flight.end_time
                    q.append(flight.cityB)

    def get_min_cost(self, cityA, cityB):
        pass

test = Graph()
graph = test.graph
print(graph)
# for name, flight_list in graph.items():