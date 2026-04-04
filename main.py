from map.map import Graph
from datetime import timedelta
from datetime import datetime

map = Graph(flight_delay=timedelta(0), file_path="map/flights.json")
# print(map)
date = datetime.strptime("01.07.2027 00:00", "%d.%m.%Y %H:%M")
lst1 = map.get_min_duration("Moscow", "Vladivostok", date, transport_list=[1])
lst2 = map.get_min_changes("Moscow", "Vladivostok", date, transport_list=[1, 2])
lst3 = map.get_min_cost("Moscow", "Vladivostok", date, transport_list=[2, 3])
lst4 = map.get_straight_races("Moscow", "Vladivostok", date, transport_list=[1, 2])
# for name, flight_list in graph.items():
print(*lst1)
print('--'*30 + '\n')
print(*lst2)
print('--'*30 + '\n')
print(*lst3)
print('--'*30 + '\n')
print(*lst4)
