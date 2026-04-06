from map.map import Graph
from datetime import timedelta, timezone, datetime

map = Graph(flight_delay=timedelta(0), file_path="map/flights.json")
# print(map)
date = datetime.fromisoformat("2026-04-06T21:00:00+01:00")
date2 = datetime.fromisoformat("2026-04-05T21:12:00+01:00")
lst1 = map.get_min_duration("Москва", "Екатеринбург", date, date2, transport_list=[1, 4])
lst2 = map.get_min_changes("Москва", "Санкт-Петербург", date, transport_list=[1, 2, 3])
lst3 = map.get_min_cost("Москва", "Санкт-Петербург", date, transport_list=[1, 2, 3])
lst4 = map.get_straight_races("Екатеринбург", "Челябинск", date, transport_list=[1, 2, 3])
lst5 = map.get_all_moves('Москва', date)
# for name, flight_list in graph.items():
# print(*lst1)
print('--'*65 + '\n')
# print(*lst2)
print('--'*65 + '\n')
# print(*lst3)
print('--'*65 + '\n')
print(*lst4)
print('--'*65 + '\n')
lst = map.forward_back_routes('Москва', 'Санкт-Петербург', date, date2)
# for fligh1, fligh2 in lst:
#     print(fligh1)
#     print(fligh2)
#     print('--' * 65 + '\n')
