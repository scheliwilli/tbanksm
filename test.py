import streamlit as st
from datetime import datetime, timezone
from map.map import Graph

#   Иницилизация
mapp = Graph()
cities_list = list(mapp.graph.keys())
st.set_page_config(
    layout="wide", 
    )

icons = {
    "filter" : r"pictures\sort.svg",
    "rzd" : r"pictures\rzd.svg",
    "s7" : r"pictures\s7.svg",
    "logo" : r"pictures\logo.svg"
}
priorities = ["Выгоднее", "Минимум пересадок", "Ближайшее прибытие"]

#   Выбор транспорта
transport_dict = {
    "🚂 Поезд" : 1,
    "✈️ Самолёт" : 2,
    "🚌 Автобус" : 3,
    "🚞 Пригород" : 4
}

#   Устанавливаем начало страницы
col1, col2 = st.columns([1, 10])
with col1:
    st.image(icons["logo"])
with col2:
    st.title("Добропожаловать в конструктор маршрутов Т-маршрутер!", text_alignment="left")

#   основа
col1, col2, col3 = st.columns([5, 5, 7])

#   Поле ввода городов
with col1:
    st.header("🛫 Отправление: ")
    cityA = st.selectbox("🏙️ Введите город отправления: ", cities_list)
with col2:
    st.header("🛬 Прибытие: ")
    cityB = st.selectbox("🏙️ Введите город назначения: ", cities_list)
#   Поле ввода дат
with col1:
    start_date = st.date_input("🗓️ Выберите дату отправленя: ")
with col2:
    arrive_date = st.date_input("🗓️ Выберите дату прибытия: ")
#   Картинка:
with col3:
    st.image(icons["rzd"])
    st.image(icons['s7'])

start_date = datetime(
    start_date.year, 
    start_date.month,
    start_date.day,
    tzinfo=timezone.utc)
    
arrive_date = datetime(
    arrive_date.year, 
    arrive_date.month,
    arrive_date.day,
    tzinfo=timezone.utc)

#   Устанавливаем поля
transport_col, filter_col = st.columns([2, 1])

#   Выбор транспорта
with transport_col:
    transport_names = transport_dict.keys()
    chosed_ransport = st.multiselect("Выберите свой транспорт", transport_dict)
    transport_id = [transport_dict[name] for name in chosed_ransport]

#   Выбор фильтра
with filter_col:
    priority = st.selectbox(f"![icon](pictures/sort.svg)", priorities)

#   Выводим
find = st.button("Найти рейсы")

if (find):
    route = mapp.get_min_cost(
        cityA=cityA,
        cityB=cityB,
        departure_time=start_date,
        arrivetime=arrive_date,
        transport_list=transport_id
    )
    st.success(*route)