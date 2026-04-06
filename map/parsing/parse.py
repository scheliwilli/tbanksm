import requests # для работы  с API
import json # для сохранения данных
from datetime import timedelta, timezone, datetime, date # для работы с датой и рвременем
from time import time
import re  


def string2UTC(string:str):
    utc_time = datetime.fromisoformat(string)


def UTC2Local(utc_time, delta_utc):
    pass


transport_dict = {
    "train" : 1,
    "plane" : 2,
    "bus" : 3,
    "suburban" : 4
}


class Parser():
    def __init__ (
            self,
            DATES:list,
            API_KEY="020aed89-3a0b-4c4e-8766-ce988f42c520",
            path4flights=r"C:\Users\nikit\OneDrive\Документы\УЧЕБА\tbanksm\tbanksm\map\flights.json",
            path4cities=r"C:\Users\nikit\OneDrive\Документы\УЧЕБА\tbanksm\tbanksm\map\parsing\cities.json"
    ):
        self.API_KEY = API_KEY
        self.DATES = DATES
        # Открываем файл для чтения
        with open(path4cities, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.CITIES = data
        self.path4cities = path4cities
        self.path4flights = path4flights


    def get_routes(self, from_code, to_code, date):
        url = "https://api.rasp.yandex.net/v3.0/search/"

        params = {
            "apikey": self.API_KEY,
            "from": from_code, # код города отправления
            "to": to_code, # код города назначения
            "format": "json",
            "lang": "ru_RU",
            "date": date,         # дата поездки
        }

        response = requests.get(url, params=params)
        data = response.json()

        return data.get("segments", [])


    def get_routes(self, from_code: str, to_code: str, date: str):
        url = "https://api.rasp.yandex-net.ru/v3.0/search/"

        params = {
            "apikey": self.API_KEY,
            "from": from_code,
            "to": to_code,
            "format": "json",
            "lang": "ru_RU",
            "date": date,  # YYYY-MM-DD
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data.get("segments", [])
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса {from_code} -> {to_code} на {date}: {e}")
            return []

    def process_segments(self, segments, from_name, to_name):
        routes = []
        seen = set()

        for s in segments:
            thread = s.get("thread", {})
            transport = thread.get("transport_type")
            number = thread.get("number")

            carrier = thread.get("carrier")
            company = carrier.get("title") if carrier else None
            company_url = carrier.get("url") if carrier else None

            dep = s.get("departure")
            arr = s.get("arrival")

            if not dep or not arr:
                continue

            key = (transport, number, dep, arr)
            if key in seen:
                continue
            seen.add(key)

            try:
                t1 = datetime.fromisoformat(dep)
                t2 = datetime.fromisoformat(arr)
                duration = int((t2 - t1).total_seconds() / 60)
            except Exception:
                duration = None

            #   Меняем формат данных
            transport = transport_dict[transport]

            routes.append({
                "from": from_name,
                "to": to_name,
                "type": transport,
                "company": company,
                "company_url" : company_url,
                "number": number,
                "departure": dep,
                "arrival": arr,
                "duration": duration
            })

        return routes

    def update_flights(self):
        all_routes = {}

        for from_name in self.CITIES:
            all_routes[from_name] = []
            #   Записываем пока пустые массивы
            with open(self.path4flights, "w", encoding="utf-8") as f:
                json.dump(all_routes, f, ensure_ascii=False, indent=2)

        for date in self.DATES:
            print(f"Дата: {date}")

            for from_name, from_code in self.CITIES.items():
                #   Читаем уже записанное
                with open(self.path4flights, "r", encoding="utf-8") as f:
                    all_routes = json.load(f)

                for to_name, to_code in self.CITIES.items():
                    if from_name == to_name:
                        continue

                    print(f"{from_name} -> {to_name}")

                    segments = self.get_routes(from_code, to_code, date)
                    print("Найдено:", len(segments))

                    routes = self.process_segments(segments, from_name, to_name)
                    all_routes[from_name].extend(routes)
                    # time.sleep(0.02)
                
                #   Записываем с нуля уже спарсенное
                with open(self.path4flights, "w", encoding="utf-8") as f:
                    json.dump(all_routes, f, ensure_ascii=False, indent=2)

        print("Готово. Городов в результате:", len(all_routes))


    def update_transport_type(self):
        #   Хаваем
        with open(self.path4flights, "r", encoding="utf-8") as f:
            routes = json.load(f)

        for city, route_list in routes.items():
            for route in route_list:
                route["type"] = transport_dict[route["type"]]

        #   Записываем
        with open(self.path4flights, "w", encoding="utf-8") as f:
            json.dump(routes, f, ensure_ascii=False, indent=2)


def get_date_range(datedelta=14, start_date=date.today()):
    dates = [start_date + timedelta(delta) for delta in range(datedelta)]
    dates = list(map(str, dates))
    return dates


parser = Parser(
    DATES=get_date_range(5),
    API_KEY="1ab02b59-e89c-4584-82a8-d45acae4ba61",
    path4flights=r"C:\Users\nikit\OneDrive\Документы\УЧЕБА\tbanksm\tbanksm\map\flights.json",
    path4cities=r"C:\Users\nikit\OneDrive\Документы\УЧЕБА\tbanksm\tbanksm\map\parsing\cities.json"
)

# parser.update_flights()
parser.update_transport_type()