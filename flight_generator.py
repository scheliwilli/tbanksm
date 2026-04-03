import json
import random
from datetime import datetime, timedelta

# Список реальных городов России (300 штук)
cities = [
    "Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan", "Nizhny Novgorod",
    "Chelyabinsk", "Omsk", "Samara", "Rostov-on-Don", "Ufa", "Krasnoyarsk", "Perm", "Voronezh",
    "Volgograd", "Krasnodar", "Saratov", "Tyumen", "Tolyatti", "Izhevsk", "Barnaul", "Ulyanovsk",
    "Irkutsk", "Khabarovsk", "Yaroslavl", "Vladivostok", "Makhachkala", "Tomsk", "Orenburg",
    "Kemerovo", "Novokuznetsk", "Ryazan", "Astrakhan", "Naberezhnye Chelny", "Penza", "Lipetsk",
    "Kirov", "Cheboksary", "Kaliningrad", "Tula", "Kursk", "Stavropol", "Ulan-Ude", "Sochi",
    "Magnitogorsk", "Ivanovo", "Bryansk", "Tver", "Belgorod", "Sevastopol", "Nizhny Tagil",
    "Arkhangelsk", "Vladimir", "Murmansk", "Kaluga", "Chita", "Grozny", "Smolensk", "Kostroma",
    "Kurgan", "Orel", "Volzhsky", "Cherepovets", "Vologda", "Saransk", "Tambov", "Vladikavkaz",
    "Yakutsk", "Podolsk", "Petrozavodsk", "Balashikha", "Khimki", "Yoshkar-Ola", "Blagoveshchensk",
    "Korolyov", "Berezniki", "Mytishchi", "Lyubertsy", "Novorossiysk", "Nalchik", "Stary Oskol",
    "Syktyvkar", "Noyabrsk", "Prokopyevsk", "Biysk", "Krasnogorsk", "Pskov", "Angarsk", "Balakovo",
    "Dzerzhinsk", "Orekhovo-Zuyevo", "Bratsk", "Armavir", "Veliky Novgorod", "Surgut", "Zlatoust",
    "Khanty-Mansiysk", "Nizhnevartovsk", "Novy Urengoy", "Yuzhno-Sakhalinsk", "Magadan", "Petropavlovsk-Kamchatsky"
]
# Повторяем, чтобы получить 300 уникальных (добавим ещё из малых городов)
more_cities = [
    "Abakan", "Anadyr", "Birobidzhan", "Cherkessk", "Elista", "Gorno-Altaysk", "Kyzyl",
    "Maykop", "Naryan-Mar", "Saransk", "Ufa", "Ulan-Ude", "Yoshkar-Ola", "Barnaul",
    "Vladivostok", "Volgograd", "Voronezh", "Yekaterinburg", "Izhevsk", "Irkutsk",
    "Kazan", "Kemerovo", "Kirov", "Krasnodar", "Krasnoyarsk", "Kurgan", "Kursk",
    "Lipetsk", "Moscow", "Murmansk", "Nizhny Novgorod", "Novosibirsk", "Omsk",
    "Orenburg", "Oryol", "Penza", "Perm", "Rostov-on-Don", "Ryazan", "Samara",
    "Saint Petersburg", "Saratov", "Smolensk", "Sochi", "Stavropol", "Syktyvkar",
    "Tambov", "Tomsk", "Tula", "Tver", "Tyumen", "Ulyanovsk", "Volgograd", "Voronezh"
]
cities = list(dict.fromkeys(cities + more_cities))

def random_date(start_year=2027, end_year=2027):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    dt = start + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
    return dt.strftime("%d.%m.%Y %H:%M")

def flight_duration_hours(dep, arr, transport_type):
    # Приблизительная длительность в зависимости от расстояния и типа
    # Для простоты используем случайную логику
    base_hours = random.uniform(1, 12)
    if transport_type == 1:  # поезд - дольше
        base_hours *= 1.5
    elif transport_type == 3:  # электричка - короткие расстояния
        base_hours = random.uniform(0.5, 4)
    return base_hours

# Генерация данных
data = {}
next_id = 1

for origin in cities:
    flights = []
    # Для каждого города-отправления генерируем 300 рейсов в разные города
    destinations = [c for c in cities if c != origin]
    for _ in range(300):
        dest = random.choice(destinations)
        transport = random.choice([1, 2, 3])  # 1=поезд, 2=самолёт, 3=электричка
        # Базовая цена (условно)
        price = random.randint(2000, 35000)
        # Корректировка цены по типу транспорта
        if transport == 1:      # поезд дешевле самолёта
            price = int(price * 0.7)
        elif transport == 3:    # электричка ещё дешевле
            price = int(price * 0.3)
        price = max(500, min(50000, price))
        
        departure = random_date()
        # Длительность полёта/поездки
        duration_h = flight_duration_hours(departure, None, transport)
        # Примерно считаем время прибытия
        dep_dt = datetime.strptime(departure, "%d.%m.%Y %H:%M")
        arr_dt = dep_dt + timedelta(hours=duration_h)
        arrival = arr_dt.strftime("%d.%m.%Y %H:%M")
        
        seats = random.randint(1, 5)  # количество мест
        
        flights.append([origin, dest, departure, arrival, price, next_id, seats, transport])
        next_id += 1
    data[origin] = flights

# Сохраняем в JSON
with open("flights.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Сгенерировано {len(data)} городов, всего рейсов: {next_id-1}")