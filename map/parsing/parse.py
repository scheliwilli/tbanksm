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
            API_KEYS:list,
            path4flights=r"C:\Users\nikit\OneDrive\Документы\УЧЕБА\tbanksm\tbanksm\map\flights.json",
            path4cities=r"C:\Users\nikit\OneDrive\Документы\УЧЕБА\tbanksm\tbanksm\map\parsing\cities.json"
    ):
        self.API_KEYS = API_KEYS
        self.cur_key_id = 0
        self.cur_key = API_KEYS[self.cur_key_id]
        self.DATES = DATES
        # Открываем файл для чтения
        with open(path4cities, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.CITIES = data
        self.path4cities = path4cities
        self.path4flights = path4flights


    def rotate_key(self):
        self.cur_key_id += 1
        if (self.cur_key_id < len(API_KEYS)):
            self.cur_key = self.API_KEYS[self.cur_key_id]
            print(f"Меняем ключ. Актуальный {self.cur_key_id}:", self.cur_key)

    
    def has_free_keys(self):
        return (self.cur_key_id < len(API_KEYS))
            


    def get_routes(self, from_code, to_code, date):
        url = "https://api.rasp.yandex.net/v3.0/search/"

        params = {
            "apikey": self.cur_key,
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
            "apikey": self.cur_key,
            "from": from_code,
            "to": to_code,
            "format": "json",
            "lang": "ru_RU",
            "date": date,  # YYYY-MM-DD
        }

        try:
            t0 = time()
            response = requests.get(url, params=params, timeout=20)
            t1 = time()
            print(f"Один API запрос обрабатывался {t1 - t0} секунд") #   Лог
            response.raise_for_status()
            data = response.json()
            return data.get("segments", [])
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:
                # лимит — переключаем ключ
                self.rotate_key()

            elif response.status_code == 403:
                error_code = response.json().get("error", {}).get("code")

                if error_code in ["invalid_api_key", "missing_api_key"]:
                    # ключ умер — удаляем из пула
                    self.rotate_key()

                else:
                    # другая 403
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

                    #   Проверка наличия ключей после додепа:
                    if not self.has_free_keys(): break

                    routes = self.process_segments(segments, from_name, to_name)
                    all_routes[from_name].extend(routes)
                    # time.sleep(0.02)
                
                #   Записываем с нуля уже спарсенное
                with open(self.path4flights, "w", encoding="utf-8") as f:
                    json.dump(all_routes, f, ensure_ascii=False, indent=2)
                #   Проверка наличия ключей после додепа:
                if not self.has_free_keys(): break
            #   Проверка наличия ключей после додепа:
            if not self.has_free_keys(): 
                print("API ключи закончились!")
                break

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


    def load_flights(self):
        routes = {}
        #   Хаваем
        print("Загружаем файл")
        with open(self.path4flights, "r", encoding="utf-8") as f:
            routes = json.load(f)
            print("Файл загружен")
        return routes
    

    def dump_flights(self, routes: dict):
        #   Записываем
        print("Записываем файл")
        with open(self.path4flights, "w", encoding="utf-8") as f:
            json.dump(routes, f, ensure_ascii=False, indent=2)
            print("Файл записан")


    def multiply_data(self, day_step:int):
        routes = self.load_flights()
        new_routes = routes
        for from_city, route_list in routes.items():
            for route in route_list:
                new_route = route
                new_route["departure"] = str(datetime.fromisoformat(route["departure"]) + timedelta(days=day_step))
                new_route["arrival"] = str(datetime.fromisoformat(route["arrival"])+ timedelta(days=day_step))
                new_routes[from_city].append(new_route)
                print("Обработан маршрут", from_city, route["to"])
            print(from_city, "Обработан")
        new_route.dump_flights(self)
        

def get_date_range(datedelta=14, start_date=date.today()):
    dates = [start_date + timedelta(delta) for delta in range(datedelta)]
    dates = list(map(str, dates))
    return dates


API_KEYS = [
    "1ab02b59-e89c-4584-82a8-d45acae4ba61",
    "020aed89-3a0b-4c4e-8766-ce988f42c520",
    "d5f6c293-846e-4a7e-9284-b75933178188",
    "c2a50af4-c0ef-4990-a918-c638dbedf83f",
    "f929956f-faae-48b9-9bdc-20fdf37bee57",
    "eb5ca38b-8424-4852-a59b-325602fae6fa",
    "b2cb6002-dbe1-4439-af20-823432d15960"
]

parser = Parser(
    DATES=get_date_range(2),
    API_KEYS=API_KEYS,
    path4flights=r"C:\Users\nikit\OneDrive\Документы\УЧЕБА\tbanksm\tbanksm\map\flights.json",
    path4cities=r"C:\Users\nikit\OneDrive\Документы\УЧЕБА\tbanksm\tbanksm\map\parsing\cities.json"
)

# parser.update_flights()
parser.multiply_data(day_step=2)
# parser.multiply_data(day_step=4)
# parser.multiply_data(day_step=8)