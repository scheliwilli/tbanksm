from map.map import Graph
from datetime import timedelta
from datetime import datetime

map = Graph(flight_delay=timedelta(0), file_path="map/flights.json")
# print(map)
date = datetime.strptime("01.01.2020 00:00", "%d.%m.%Y %H:%M")
lst1 = map.get_min_duration("Moscow", "Vladivostok", date)
lst2 = map.get_min_changes("Moscow", "Vladivostok", date)
lst3 = map.get_min_cost("Moscow", "Vladivostok", date)

# for name, flight_list in graph.items():
print(*lst1)
print('--'*30 + '\n')
print(*lst2)
print('--'*30 + '\n')
print(*lst3)
