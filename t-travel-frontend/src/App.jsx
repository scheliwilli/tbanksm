import { useEffect, useMemo, useRef, useState } from 'react';
import { getCities, getClientContext, getFlightsFromCity, getItinerary, getRoutes } from './api';
import FlightCatalog from './components/FlightCatalog';
import HighlightFlags from './components/HighlightFlags';
import Modal from './components/Modal';
import TicketCard from './components/TicketCard';
import {
  apiDateToUi,
  formatClientLocation,
  formatDisplayDate,
  formatDuration,
  formatPrice,
  formatStayHours,
  formatTransfers,
  uiDateToApi,
} from './utils';

import logo from '../logo.svg';
import calendarIcon from '../calendar.svg';
import sortIcon from '../sort.svg';
import swapIcon from '../strelki.svg';
import rzdImage from '../rzd.svg';
import s7Image from '../s7.svg';

const transportTiles = [
  { key: 'train', label: 'Ж/д билеты', image: rzdImage },
  { key: 'plane', label: 'Авиабилеты', image: s7Image },
];

const searchModes = [
  { key: 'single', label: 'Обычный поиск' },
  { key: 'catalog', label: 'Каталог рейсов' },
  { key: 'itinerary', label: 'Маршрут по городам' },
];

const sortOptions = [
  { value: 'cost', label: 'Сначала дешевле' },
  { value: 'duration', label: 'Сначала быстрее' },
  { value: 'transfers', label: 'Меньше пересадок' },
  { value: 'departure', label: 'По времени отправления' },
  { value: 'closest_time', label: 'Ближайшее время' },
];
const NO_SORT_VALUE = 'none';

const initialFilters = {
  max_transfers: 3,
  min_cost: '',
  max_cost: '',
  min_duration: '',
  max_duration: '',
};

let nextStopId = 1;

function makeStop() {
  return {
    id: nextStopId++,
    city: '',
    stayHours: 24,
  };
}

function formatCount(count, forms) {
  const mod100 = count % 100;
  const mod10 = count % 10;

  if (mod100 >= 11 && mod100 <= 14) {
    return forms[2];
  }

  if (mod10 === 1) {
    return forms[0];
  }

  if (mod10 >= 2 && mod10 <= 4) {
    return forms[1];
  }

  return forms[2];
}

function getHighlightScore(item) {
  return Number(Boolean(item.isCheapest)) + Number(Boolean(item.isFastest));
}

function prioritizeHighlightedItems(items) {
  return items
    .map((item, index) => ({ item, index }))
    .sort((left, right) => {
      const highlightDiff = getHighlightScore(right.item) - getHighlightScore(left.item);
      if (highlightDiff !== 0) {
        return highlightDiff;
      }

      return left.index - right.index;
    })
    .map(({ item }) => item);
}

function dedupeItemsByKey(items, makeKey) {
  const seenKeys = new Set();
  const uniqueItems = [];

  for (const item of items) {
    const key = makeKey(item);
    if (seenKeys.has(key)) {
      continue;
    }

    seenKeys.add(key);
    uniqueItems.push(item);
  }

  return uniqueItems;
}

function getFlightListKey(flight) {
  return [
    flight.from,
    flight.to,
    flight.id || '',
    flight.departure_iso || '',
    flight.arrival_iso || '',
    flight.transport || '',
  ].join('|');
}

function getRouteKey(route) {
  return route.segments
    .map((segment) => getFlightListKey(segment))
    .join('::');
}

function buildFlightCatalogs(flights, selectedDate, selectedTransport) {
  const filteredFlights = flights.filter((flight) => {
    const matchesDate = !selectedDate || flight.departure_iso?.slice(0, 10) === selectedDate;
    const matchesTransport = selectedTransport.length === 0 || selectedTransport.includes(flight.transport);
    return matchesDate && matchesTransport;
  });
  const uniqueFlights = dedupeItemsByKey(filteredFlights, getFlightListKey);

  const groupedFlights = uniqueFlights.reduce((accumulator, flight) => {
    const destination = flight.to || 'Без направления';
    if (!accumulator.has(destination)) {
      accumulator.set(destination, []);
    }

    accumulator.get(destination).push(flight);
    return accumulator;
  }, new Map());

  return Array.from(groupedFlights.entries())
    .map(([destination, destinationFlights]) => {
      const cheapestCost = Math.min(...destinationFlights.map((flight) => flight.cost));
      const fastestDuration = Math.min(...destinationFlights.map((flight) => flight.duration_min));
      const flightsWithFlags = destinationFlights
        .map((flight) => ({
          ...flight,
          isCheapest: flight.cost === cheapestCost,
          isFastest: flight.duration_min === fastestDuration,
        }))
        .sort((left, right) => {
          const highlightDiff = getHighlightScore(right) - getHighlightScore(left);
          if (highlightDiff !== 0) {
            return highlightDiff;
          }

          if (left.isCheapest !== right.isCheapest) {
            return left.isCheapest ? -1 : 1;
          }

          if (left.isFastest !== right.isFastest) {
            return left.isFastest ? -1 : 1;
          }

          if (left.cost !== right.cost) {
            return left.cost - right.cost;
          }

          if (left.duration_min !== right.duration_min) {
            return left.duration_min - right.duration_min;
          }

          return left.departure_iso.localeCompare(right.departure_iso);
        });
      const highlightedCount = flightsWithFlags.filter((flight) => getHighlightScore(flight) > 0).length;

      return {
        destination,
        flights: flightsWithFlags,
        count: flightsWithFlags.length,
        countLabel: `${flightsWithFlags.length} ${formatCount(flightsWithFlags.length, ['рейс', 'рейса', 'рейсов'])}`,
        cheapestCost,
        fastestDuration,
        highlightedCount,
      };
    })
    .sort((left, right) => left.destination.localeCompare(right.destination, 'ru'));
}

function ClientHint({ clientContext }) {
  const locationLabel = formatClientLocation(clientContext);
  if (!locationLabel) return null;

  return (
    <div className="location-pill">
      Время показываем для <strong>{locationLabel}</strong>
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState('single');
  const [cities, setCities] = useState([]);
  const [loadingCities, setLoadingCities] = useState(true);
  const [routeLoading, setRouteLoading] = useState(false);
  const [error, setError] = useState('');
  const [clientContext, setClientContext] = useState(null);
  const [filters, setFilters] = useState(initialFilters);
  const [draftFilters, setDraftFilters] = useState(initialFilters);
  const [sortBy, setSortBy] = useState(NO_SORT_VALUE);
  const [draftSortBy, setDraftSortBy] = useState(NO_SORT_VALUE);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isSortOpen, setIsSortOpen] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [directoryResult, setDirectoryResult] = useState(null);
  const [itineraryResult, setItineraryResult] = useState(null);
  const [hoveredTransport, setHoveredTransport] = useState(null);
  const [hoveredCatalogTransport, setHoveredCatalogTransport] = useState(null);
  const [hoveredPlannerTransport, setHoveredPlannerTransport] = useState(null);
  const [openCatalogs, setOpenCatalogs] = useState({});
  const singleDateInputRef = useRef(null);
  const directoryDateInputRef = useRef(null);
  const itineraryDateInputRef = useRef(null);

  const [form, setForm] = useState(() => ({
    origin: '',
    destination: '',
    date: '',
    transport: [],
  }));

  const [itineraryForm, setItineraryForm] = useState(() => ({
    origin: '',
    date: '',
    transport: [],
    stops: [makeStop()],
  }));

  const [catalogForm, setCatalogForm] = useState(() => ({
    origin: '',
    date: '',
    transport: [],
  }));

  useEffect(() => {
    let mounted = true;

    Promise.allSettled([getCities(), getClientContext()])
      .then(([citiesResult, clientResult]) => {
        if (!mounted) return;

        if (citiesResult.status === 'fulfilled') {
          setCities(citiesResult.value.cities || []);
        } else {
          setError(citiesResult.reason?.message || 'Не удалось загрузить список городов');
        }

        if (clientResult.status === 'fulfilled') {
          setClientContext(clientResult.value);
        }
      })
      .finally(() => {
        if (mounted) setLoadingCities(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const cityOptions = useMemo(() => [...cities].sort((a, b) => a.localeCompare(b, 'ru')), [cities]);
  const activeClientContext = searchResult?.client_context
    || directoryResult?.client_context
    || itineraryResult?.client_context
    || clientContext;
  const activeSortLabel = sortBy === NO_SORT_VALUE
    ? 'Сортировка'
    : sortOptions.find((item) => item.value === sortBy)?.label || 'Сортировка';
  const resultKind = directoryResult ? 'catalog' : itineraryResult ? 'itinerary' : searchResult ? 'single' : null;

  useEffect(() => {
    if (searchResult && !itineraryResult) {
      handleSearch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, sortBy]);

  async function runSingleSearch(overrides = {}) {
    const nextForm = {
      ...form,
      ...overrides,
    };

    if (Object.keys(overrides).length > 0) {
      setForm(nextForm);
    }

    setError('');
    setRouteLoading(true);

    try {
      const data = await getRoutes({
        origin: nextForm.origin,
        destination: nextForm.destination,
        date: uiDateToApi(nextForm.date),
        sort_by: sortBy === NO_SORT_VALUE ? undefined : sortBy,
        sort_order: 'asc',
        transport: nextForm.transport,
        max_transfers: filters.max_transfers,
        min_cost: filters.min_cost,
        max_cost: filters.max_cost,
        min_duration: filters.min_duration,
        max_duration: filters.max_duration,
      });

      const routes = prioritizeHighlightedItems(dedupeItemsByKey(
        (data.routes || []).map((route) => ({
          ...route,
          origin: data.origin,
          destination: data.destination,
        })),
        getRouteKey,
      ));

      setSearchResult({ ...data, routes });
      setDirectoryResult(null);
      setItineraryResult(null);
      setClientContext((current) => data.client_context || current);
    } catch (err) {
      setSearchResult(null);
      setError(err.message);
    } finally {
      setRouteLoading(false);
    }
  }

  async function handleSearch(event) {
    event?.preventDefault();
    await runSingleSearch();
  }

  async function handleItinerarySearch(event) {
    event?.preventDefault();
    setError('');
    setRouteLoading(true);

    try {
      const data = await getItinerary({
        origin: itineraryForm.origin,
        date: uiDateToApi(itineraryForm.date),
        transport: itineraryForm.transport,
        max_transfers: filters.max_transfers,
        stops: itineraryForm.stops.map((stop) => ({
          city: stop.city,
          stay_hours: Number(stop.stayHours) || 0,
        })),
      });

      setItineraryResult(data);
      setSearchResult(null);
      setDirectoryResult(null);
      setClientContext((current) => data.client_context || current);
      if (!data.found && data.message) {
        setError(data.message);
      }
    } catch (err) {
      setItineraryResult(null);
      setError(err.message);
    } finally {
      setRouteLoading(false);
    }
  }

  async function handleCatalogSearch(event) {
    event?.preventDefault();
    setError('');
    setRouteLoading(true);

    try {
      const data = await getFlightsFromCity(catalogForm.origin);
      const catalogs = buildFlightCatalogs(data.flights || [], catalogForm.date, catalogForm.transport);
      const totalFlights = catalogs.reduce((sum, catalog) => sum + catalog.flights.length, 0);

      setDirectoryResult({
        origin: data.city,
        selectedDate: catalogForm.date,
        transport: [...catalogForm.transport],
        totalFlights,
        totalDestinations: catalogs.length,
        catalogs,
        client_context: data.client_context,
      });
      setSearchResult(null);
      setItineraryResult(null);
      setOpenCatalogs({});
      setClientContext((current) => data.client_context || current);
    } catch (err) {
      setDirectoryResult(null);
      setError(err.message);
    } finally {
      setRouteLoading(false);
    }
  }

  function updateForm(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateCatalogForm(key, value) {
    setCatalogForm((current) => ({ ...current, [key]: value }));
  }

  function updateItineraryForm(key, value) {
    setItineraryForm((current) => ({ ...current, [key]: value }));
  }

  function updateStop(index, key, value) {
    setItineraryForm((current) => ({
      ...current,
      stops: current.stops.map((stop, stopIndex) => (
        stopIndex === index
          ? { ...stop, [key]: value }
          : stop
      )),
    }));
  }

  function addStop() {
    setItineraryForm((current) => ({
      ...current,
      stops: [...current.stops, makeStop()],
    }));
  }

  function removeStop(index) {
    setItineraryForm((current) => ({
      ...current,
      stops: current.stops.filter((_, stopIndex) => stopIndex !== index),
    }));
  }

  function toggleTransport(stateKey, type) {
    const setterByMode = {
      single: setForm,
      catalog: setCatalogForm,
      itinerary: setItineraryForm,
    };
    const setter = setterByMode[stateKey];
    if (!setter) return;

    setter((current) => {
      const isActive = current.transport.includes(type);
      return {
        ...current,
        transport: isActive
          ? current.transport.filter((item) => item !== type)
          : [...current.transport, type],
      };
    });
  }

  function swapCities() {
    setForm((current) => ({
      ...current,
      origin: current.destination,
      destination: current.origin,
    }));
  }

  function resetSearch() {
    setSearchResult(null);
    setDirectoryResult(null);
    setItineraryResult(null);
    setOpenCatalogs({});
    setError('');
  }

  function toggleCatalog(destination) {
    setOpenCatalogs((current) => ({
      ...current,
      [destination]: !current[destination],
    }));
  }

  function openFilters() {
    setDraftFilters(filters);
    setIsFilterOpen(true);
  }

  function applyFilters() {
    setFilters(draftFilters);
    setIsFilterOpen(false);
  }

  function openSort() {
    setDraftSortBy(sortBy);
    setIsSortOpen(true);
  }

  function applySort() {
    setSortBy(draftSortBy);
    setIsSortOpen(false);
  }

  function resetSort() {
    setDraftSortBy(NO_SORT_VALUE);
    setSortBy(NO_SORT_VALUE);
    setIsSortOpen(false);
  }

  function applyFlexibleDate(date) {
    runSingleSearch({ date: apiDateToUi(date) });
  }

  function openDatePicker(ref) {
    const input = ref.current;
    if (!input) return;

    input.focus();
    if (typeof input.showPicker === 'function') {
      input.showPicker();
      return;
    }
    input.click();
  }

  function renderTransportTiles(transportStateKey, hoveredState, setHoveredState, selectedTransport) {
    return (
      <div className="search-card__mediaside">
        {transportTiles.map((tile) => {
          const isSelected = selectedTransport.includes(tile.key);
          const isHovered = hoveredState === tile.key;

          return (
            <button
              key={tile.key}
              type="button"
              className={`transport-tile ${isSelected ? 'is-selected' : ''} ${isHovered ? 'is-hovered' : ''}`}
              onMouseEnter={() => setHoveredState(tile.key)}
              onMouseLeave={() => setHoveredState(null)}
              onFocus={() => setHoveredState(tile.key)}
              onBlur={() => setHoveredState(null)}
              onClick={() => toggleTransport(transportStateKey, tile.key)}
              aria-pressed={isSelected}
            >
              <img src={tile.image} alt={tile.label} />
              <span>{tile.label}</span>
            </button>
          );
        })}
      </div>
    );
  }

  function renderCompactTransportGrid(transportStateKey, hoveredState, setHoveredState, selectedTransport) {
    return (
      <div className="planner-card__transport">
        <div className="planner-card__label">Транспорт</div>
        <div className="planner-transport-grid">
          {transportTiles.map((tile) => {
            const isSelected = selectedTransport.includes(tile.key);
            const isHovered = hoveredState === tile.key;

            return (
              <button
                key={tile.key}
                type="button"
                className={`transport-tile transport-tile--compact ${isSelected ? 'is-selected' : ''} ${isHovered ? 'is-hovered' : ''}`}
                onMouseEnter={() => setHoveredState(tile.key)}
                onMouseLeave={() => setHoveredState(null)}
                onFocus={() => setHoveredState(tile.key)}
                onBlur={() => setHoveredState(null)}
                onClick={() => toggleTransport(transportStateKey, tile.key)}
                aria-pressed={isSelected}
              >
                <img src={tile.image} alt={tile.label} />
                <span>{tile.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  function renderSingleSearch() {
    return (
      <section className="hero">
        <h1>Т-Путешествия</h1>
        <ClientHint clientContext={activeClientContext} />

        <form className="search-card" onSubmit={handleSearch}>
          <div className="search-card__layout">
            <div className="search-card__formside">
              <div className="search-row search-row--cities">
                <input
                  list="cities-list"
                  className="field"
                  placeholder="Откуда"
                  value={form.origin}
                  onChange={(event) => updateForm('origin', event.target.value)}
                  required
                />

                <button
                  type="button"
                  className="swap-button"
                  onClick={swapCities}
                  aria-label="Поменять местами города"
                >
                  <img src={swapIcon} alt="" />
                </button>

                <input
                  list="cities-list"
                  className="field"
                  placeholder="Куда"
                  value={form.destination}
                  onChange={(event) => updateForm('destination', event.target.value)}
                  required
                />
              </div>

              <label className="field field--with-icon field--date">
                {/* 2026-04-06 05:11 (+07): fixed the calendar field so the custom
                    placeholder disappears after selection and the picked date stays visible. */}
                <input
                  ref={singleDateInputRef}
                  type="date"
                  className={`date-input ${!form.date ? 'date-input--empty' : ''}`}
                  value={form.date}
                  onChange={(event) => updateForm('date', event.target.value)}
                  aria-label="Дата отправления"
                  required
                />
                <span className={`field-placeholder ${form.date ? 'field-placeholder--hidden' : ''}`}>
                  Дата отправления
                </span>
                <button
                  type="button"
                  className="calendar-trigger"
                  aria-label="Открыть календарь"
                  onClick={() => openDatePicker(singleDateInputRef)}
                >
                  <img src={calendarIcon} alt="" />
                </button>
              </label>
            </div>

            {renderTransportTiles('single', hoveredTransport, setHoveredTransport, form.transport)}
          </div>

          <button
            className="search-button"
            type="submit"
            disabled={routeLoading || loadingCities}
          >
            {routeLoading ? 'Ищем…' : 'Найти'}
          </button>
        </form>

        {error && <div className="message message--error">{error}</div>}
      </section>
    );
  }

  function renderItineraryPlanner() {
    return (
      <section className="hero">
        <h1>Маршрут по нескольким городам</h1>
        <p className="hero-subtitle">
          Добавьте города в порядке посещения, укажите задержку в каждом и мы подберем самый выгодный путь по цене.
        </p>
        <ClientHint clientContext={activeClientContext} />

        <form className="planner-card" onSubmit={handleItinerarySearch}>
          <div className="planner-card__top">
            <input
              list="cities-list"
              className="field"
              placeholder="Стартовый город"
              value={itineraryForm.origin}
              onChange={(event) => updateItineraryForm('origin', event.target.value)}
              required
            />

            <label className="field field--with-icon field--date">
              <input
                ref={itineraryDateInputRef}
                type="date"
                className={`date-input ${!itineraryForm.date ? 'date-input--empty' : ''}`}
                value={itineraryForm.date}
                onChange={(event) => updateItineraryForm('date', event.target.value)}
                aria-label="Дата старта"
                required
              />
              <span className={`field-placeholder ${itineraryForm.date ? 'field-placeholder--hidden' : ''}`}>
                Дата старта
              </span>
              <button
                type="button"
                className="calendar-trigger"
                aria-label="Открыть календарь"
                onClick={() => openDatePicker(itineraryDateInputRef)}
              >
                <img src={calendarIcon} alt="" />
              </button>
            </label>
          </div>

          {renderCompactTransportGrid('itinerary', hoveredPlannerTransport, setHoveredPlannerTransport, itineraryForm.transport)}

          <div className="planner-card__label">Города и задержки</div>
          <div className="planner-stop-list">
            {itineraryForm.stops.map((stop, index) => (
              <div className="planner-stop" key={stop.id}>
                <div className="planner-stop__number">{index + 1}</div>
                <input
                  list="cities-list"
                  className="field"
                  placeholder="Город для посещения"
                  value={stop.city}
                  onChange={(event) => updateStop(index, 'city', event.target.value)}
                  required
                />
                <div className="planner-stop__stay">
                  <input
                    className="field"
                    type="number"
                    min="0"
                    max="720"
                    value={stop.stayHours}
                    onChange={(event) => updateStop(index, 'stayHours', event.target.value)}
                    placeholder="24"
                  />
                  <span>часов</span>
                </div>
                <div className="planner-stop__meta">Остановка: {formatStayHours(Number(stop.stayHours) || 0)}</div>
                {itineraryForm.stops.length > 1 && (
                  <button
                    type="button"
                    className="planner-stop__remove"
                    onClick={() => removeStop(index)}
                  >
                    Удалить
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="planner-card__actions">
            <button type="button" className="ghost-button ghost-button--inline" onClick={addStop}>
              + Добавить город
            </button>
            <button className="search-button planner-card__submit" type="submit" disabled={routeLoading || loadingCities}>
              {routeLoading ? 'Строим…' : 'Построить маршрут'}
            </button>
          </div>
        </form>

        {error && <div className="message message--error">{error}</div>}
      </section>
    );
  }

  function renderCatalogSearch() {
    return (
      <section className="hero">
        <h1>Каталог рейсов</h1>
        <p className="hero-subtitle">
          Введите город отправления и дату. Сначала покажем направления, а по клику откроем рейсы внутри каждого.
        </p>
        <ClientHint clientContext={activeClientContext} />

        <form className="planner-card planner-card--catalog" onSubmit={handleCatalogSearch}>
          <div className="planner-card__top">
            <input
              list="cities-list"
              className="field"
              placeholder="Город отправления"
              value={catalogForm.origin}
              onChange={(event) => updateCatalogForm('origin', event.target.value)}
              required
            />

            <label className="field field--with-icon field--date">
              <input
                ref={directoryDateInputRef}
                type="date"
                className={`date-input ${!catalogForm.date ? 'date-input--empty' : ''}`}
                value={catalogForm.date}
                onChange={(event) => updateCatalogForm('date', event.target.value)}
                aria-label="Дата отправления"
                required
              />
              <span className={`field-placeholder ${catalogForm.date ? 'field-placeholder--hidden' : ''}`}>
                Дата отправления
              </span>
              <button
                type="button"
                className="calendar-trigger"
                aria-label="Открыть календарь"
                onClick={() => openDatePicker(directoryDateInputRef)}
              >
                <img src={calendarIcon} alt="" />
              </button>
            </label>
          </div>

          {renderCompactTransportGrid('catalog', hoveredCatalogTransport, setHoveredCatalogTransport, catalogForm.transport)}

          <div className="catalog-search__actions">
            <button className="search-button planner-card__submit" type="submit" disabled={routeLoading || loadingCities}>
              {routeLoading ? 'Собираем…' : 'Показать направления'}
            </button>
          </div>
        </form>

        {error && <div className="message message--error">{error}</div>}
      </section>
    );
  }

  function renderSingleResults() {
    const dateLabel = formatDisplayDate(searchResult?.date || form.date);
    const totalFound = searchResult.total_found ?? searchResult.count;
    const flexibleDates = searchResult.flexible_dates || [];

    return (
      <section className="results-view">
        <div className="results-head">
          <div>
            <button className="link-back" onClick={resetSearch}>
              ← Назад
            </button>
            <h1>Подходящие билеты</h1>
            <p>
              {searchResult.origin} → {searchResult.destination}
              {dateLabel ? ` · ${dateLabel}` : ''}
              {' · '}
              {totalFound} {totalFound === 1 ? 'маршрут' : totalFound < 5 ? 'маршрута' : 'маршрутов'}
            </p>
          </div>

          <div className="results-actions">
            <button className="ghost-button" onClick={openSort}>
              <img src={sortIcon} alt="" />
              {activeSortLabel}
            </button>
            <button className="ghost-button" onClick={openFilters}>
              Фильтры
            </button>
          </div>
        </div>

        <ClientHint clientContext={searchResult.client_context || activeClientContext} />

        {searchResult.is_truncated && (
          <div className="message message--hint">
            Показываем первые {searchResult.count} маршрутов из {totalFound}, чтобы список оставался быстрым и удобным.
          </div>
        )}

        <div className="filters-summary">
          <span>Пересадки: до {filters.max_transfers}</span>
          {(filters.min_cost || filters.max_cost) && (
            <span>
              Цена: {filters.min_cost || '0'} — {filters.max_cost || '∞'} ₽
            </span>
          )}
          {(filters.min_duration || filters.max_duration) && (
            <span>
              В пути: {filters.min_duration || '0'} — {filters.max_duration || '∞'} мин
            </span>
          )}
        </div>

        {error && <div className="message message--error">{error}</div>}

        {!error && searchResult.routes.length === 0 && (
          <div className="empty-state">
            <div className="empty-state__body">
              <h2>Маршруты не найдены</h2>
              <p>
                {flexibleDates.length > 0
                  ? 'На выбранную дату маршрутов нет, но мы нашли ближайшие варианты до и после.'
                  : 'Попробуйте изменить дату, тип транспорта или фильтры.'}
              </p>

              {flexibleDates.length > 0 && (
                <div className="flexible-date-panel">
                  <div className="flexible-date-panel__title">Гибкая дата</div>

                  <div className="flexible-date-actions">
                    {flexibleDates.map((option) => (
                      <button
                        key={`${option.direction}-${option.date}`}
                        type="button"
                        className="flexible-date-button"
                        onClick={() => applyFlexibleDate(option.date)}
                        disabled={routeLoading}
                      >
                        <span className="flexible-date-button__label">
                          {option.direction === 'before' ? 'Раньше' : 'Позже'}
                        </span>
                        <strong className="flexible-date-button__date">{formatDisplayDate(option.date)}</strong>
                        <span className="flexible-date-button__count">
                          {option.count} {formatCount(option.count, ['маршрут', 'маршрута', 'маршрутов'])}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="tickets-grid">
          {searchResult.routes.map((route, index) => (
            <TicketCard key={`${route.departure_iso}-${route.arrival_iso}-${index}`} route={route} />
          ))}
        </div>
      </section>
    );
  }

  function renderCatalogResults() {
    const transportSummary = transportTiles
      .filter((tile) => directoryResult.transport.includes(tile.key))
      .map((tile) => tile.label)
      .join(', ');
    const destinationsLabel = formatCount(directoryResult.totalDestinations, ['направление', 'направления', 'направлений']);
    const flightsLabel = formatCount(directoryResult.totalFlights, ['рейс', 'рейса', 'рейсов']);

    return (
      <section className="results-view">
        <div className="results-head">
          <div>
            <button className="link-back" onClick={resetSearch}>
              ← Назад
            </button>
            <h1>Каталог направлений</h1>
            <p>
              {directoryResult.origin}
              {directoryResult.selectedDate ? ` · ${formatDisplayDate(directoryResult.selectedDate)}` : ''}
              {' · '}
              {directoryResult.totalDestinations} {destinationsLabel}
              {' · '}
              {directoryResult.totalFlights} {flightsLabel}
            </p>
          </div>
        </div>

        <ClientHint clientContext={directoryResult.client_context || activeClientContext} />

        <div className="message message--hint">
          Флажки показывают самый дешевый и самый быстрый рейс внутри каждого направления. Такие рейсы подняты наверх.
        </div>

        <div className="filters-summary">
          <span>{directoryResult.totalDestinations} {destinationsLabel}</span>
          <span>{directoryResult.totalFlights} {flightsLabel}</span>
          {transportSummary && <span>Транспорт: {transportSummary}</span>}
        </div>

        {error && <div className="message message--error">{error}</div>}

        {!error && directoryResult.catalogs.length === 0 && (
          <div className="empty-state">
            <h2>Рейсы не найдены</h2>
            <p>Попробуйте изменить дату или снять фильтр по транспорту.</p>
          </div>
        )}

        <div className="catalog-grid">
          {directoryResult.catalogs.map((catalog) => (
            <FlightCatalog
              key={catalog.destination}
              catalog={catalog}
              isOpen={Boolean(openCatalogs[catalog.destination])}
              onToggle={() => toggleCatalog(catalog.destination)}
            />
          ))}
        </div>
      </section>
    );
  }

  function renderItineraryResults() {
    const itineraryStops = itineraryResult?.stops || [];

    return (
      <section className="results-view">
        <div className="results-head">
          <div>
            <button className="link-back" onClick={resetSearch}>
              ← Назад
            </button>
            <h1>Оптимальный маршрут по городам</h1>
            <p>
              {itineraryResult.origin}
              {itineraryStops.map((stop) => ` → ${stop.city}`).join('')}
              {itineraryResult.date ? ` · ${formatDisplayDate(itineraryResult.date)}` : ''}
            </p>
          </div>
        </div>

        <ClientHint clientContext={itineraryResult.client_context || activeClientContext} />

        <HighlightFlags
          isCheapest={itineraryResult.isCheapest}
          isFastest={itineraryResult.isFastest}
          className="itinerary-result__flags"
        />

        {error && <div className="message message--error">{error}</div>}

        {itineraryResult.found ? (
          <>
            <div className="itinerary-summary">
              <div>
                <span>Итоговая стоимость</span>
                <strong>от {formatPrice(itineraryResult.total_cost)}</strong>
              </div>
              <div>
                <span>Общая длительность</span>
                <strong>{formatDuration(itineraryResult.total_duration_min)}</strong>
              </div>
              <div>
                <span>Пересадки</span>
                <strong>{formatTransfers(itineraryResult.total_transfers)}</strong>
              </div>
              <div>
                <span>Остановок</span>
                <strong>{itineraryStops.length}</strong>
              </div>
            </div>

            <div className="itinerary-stop-strip">
              {itineraryStops.map((stop, index) => (
                <div className="itinerary-stop-chip" key={`${stop.city}-${index}`}>
                  <strong>{stop.city}</strong>
                  <span>{formatStayHours(stop.stay_hours)}</span>
                </div>
              ))}
            </div>

            <div className="itinerary-legs">
              {itineraryResult.legs.map((leg, index) => (
                <div className="itinerary-leg" key={`${leg.departure_iso}-${leg.arrival_iso}-${index}`}>
                  <div className="itinerary-leg__header">
                    <div>
                      <span>Этап {index + 1}</span>
                      <strong>{leg.origin} → {leg.destination}</strong>
                    </div>
                    <div>
                      <span>Остановка после прибытия</span>
                      <strong>{leg.stay_label_after_arrival}</strong>
                    </div>
                  </div>
                  <TicketCard route={leg} />
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <h2>Маршрут не найден</h2>
            <p>{itineraryResult.message || 'Попробуйте изменить список городов, дату старта или задержки.'}</p>
          </div>
        )}
      </section>
    );
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <img src={logo} alt="Т-Путешествия" className="topbar__logo" />
      </header>

      <main className={`page-content ${resultKind ? 'page-content--results' : ''}`}>
        {!resultKind && (
          <div className="mode-shell">
            <div className="mode-switch">
              {searchModes.map((searchMode) => (
                <button
                  key={searchMode.key}
                  type="button"
                  className={`mode-switch__button ${mode === searchMode.key ? 'is-active' : ''}`}
                  onClick={() => {
                    setError('');
                    setMode(searchMode.key);
                  }}
                >
                  {searchMode.label}
                </button>
              ))}
            </div>

            {mode === 'single' && renderSingleSearch()}
            {mode === 'catalog' && renderCatalogSearch()}
            {mode === 'itinerary' && renderItineraryPlanner()}
          </div>
        )}

        {resultKind === 'single' && renderSingleResults()}
        {resultKind === 'catalog' && renderCatalogResults()}
        {resultKind === 'itinerary' && renderItineraryResults()}
      </main>

      <datalist id="cities-list">
        {cityOptions.map((city) => (
          <option value={city} key={city} />
        ))}
      </datalist>

      <Modal title="Сортировка" isOpen={isSortOpen} onClose={() => setIsSortOpen(false)}>
        <div className="option-list">
          <label className="option-row">
            <input
              type="radio"
              name="sort"
              checked={draftSortBy === NO_SORT_VALUE}
              onChange={() => setDraftSortBy(NO_SORT_VALUE)}
            />
            <span>Без сортировки</span>
          </label>
          {sortOptions.map((option) => (
            <label key={option.value} className="option-row">
              <input
                type="radio"
                name="sort"
                checked={draftSortBy === option.value}
                onChange={() => setDraftSortBy(option.value)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
        <div className="modal-actions">
          <button type="button" className="ghost-button" onClick={resetSort}>Сбросить</button>
          <button type="button" className="modal-apply" onClick={applySort}>Применить</button>
        </div>
      </Modal>

      <Modal title="Фильтры" isOpen={isFilterOpen} onClose={() => setIsFilterOpen(false)}>
        <div className="filter-group">
          <label>Максимум пересадок</label>
          <input
            type="range"
            min="0"
            max="5"
            value={draftFilters.max_transfers}
            onChange={(event) => setDraftFilters((current) => ({ ...current, max_transfers: Number(event.target.value) }))}
          />
          <div className="filter-range-caption">{formatTransfers(draftFilters.max_transfers)}</div>
        </div>

        <div className="filter-grid">
          <label>
            <span>Цена от</span>
            <input
              type="number"
              value={draftFilters.min_cost}
              onChange={(event) => setDraftFilters((current) => ({ ...current, min_cost: event.target.value }))}
              placeholder="0"
            />
          </label>
          <label>
            <span>Цена до</span>
            <input
              type="number"
              value={draftFilters.max_cost}
              onChange={(event) => setDraftFilters((current) => ({ ...current, max_cost: event.target.value }))}
              placeholder="50000"
            />
          </label>
          <label>
            <span>Длительность от, мин</span>
            <input
              type="number"
              value={draftFilters.min_duration}
              onChange={(event) => setDraftFilters((current) => ({ ...current, min_duration: event.target.value }))}
              placeholder="0"
            />
          </label>
          <label>
            <span>Длительность до, мин</span>
            <input
              type="number"
              value={draftFilters.max_duration}
              onChange={(event) => setDraftFilters((current) => ({ ...current, max_duration: event.target.value }))}
              placeholder="3000"
            />
          </label>
        </div>

        <div className="filter-preview">
          <div>
            <span>Цена</span>
            <strong>
              {draftFilters.min_cost || draftFilters.max_cost
                ? `${draftFilters.min_cost || '0'} — ${draftFilters.max_cost || '∞'} ₽`
                : 'Любая'}
            </strong>
          </div>
          <div>
            <span>В пути</span>
            <strong>
              {draftFilters.min_duration || draftFilters.max_duration
                ? `${draftFilters.min_duration || '0'} — ${draftFilters.max_duration || '∞'} мин`
                : 'Любая'}
            </strong>
          </div>
        </div>

        <button className="modal-apply" onClick={applyFilters}>Применить</button>
      </Modal>
    </div>
  );
}
