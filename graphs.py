import datetime
from enum import Enum
from collections import deque

class TransportType (Enum):
    TRAIN = 1
    PLANE = 2
    ELECTRICTRAIN = 3

class parametres (Enum):
    COST = 1
    CHANGE = 2

n = int(input())

class City:
    def __init__(self, name, id):
        self.name = name
        self.id = id

class Flight:
    def __init__ (self, 
                  cityB : City, 
                  start_time : datetime, 
                  arrive_time : datetime, 
                  cost : int,
                  id: int,
                  transport_type: TransportType):
        self.cityB = cityB
        self.start_time = start_time
        self.arrive_time = arrive_time
        self.cost = cost
        self.duration = self.end_time - start_time
        self.id = id
        self.transport_type = transport_type

graph = {}
for i in range (n):
    cityA, cityB, start_time, end_time, cost = input().split(" ")
    flight = Flight(cityB, start_time, end_time, 10)
    if graph.get(cityA) == None:
        graph[cityA] = [flight]
    else:
        graph[cityA].append(flight)

def bfs (cityA:City, cityB:City, start_time):
    arrive_time = start_time
    dist = [float("inf") for i in range (len(graph)) ]
    q = deque()

    
    dist[cityA.id] = 0
    q.append(cityA)
    while (q):
        curr_city = q.popleft()
        for flight in graph[cityA]:
            if flight.start_time < arrive_time:        # Проверка успеем ли на рейс
                continue

            if dist[curr_city.id] + 1 < dist[flight.cityB.id]:
                dist[flight.cityB.id] = dist[curr_city.id] + 1
                q.append(flight.cityB)

        arrive_time = flight.arrive_time
    
    