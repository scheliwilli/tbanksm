import json

# Открываем файл для чтения
with open("citys.json", "r", encoding="utf-8") as f:
    # Загружаем данные из файла в переменную
    data = json.load(f)
print(data)
