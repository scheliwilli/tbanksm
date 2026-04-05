import { useEffect, useMemo, useRef, useState } from 'react';
import { getCities, getRoutes } from './api';
import Modal from './components/Modal';
import TicketCard from './components/TicketCard';
import { apiDateToUi, formatTransfers, uiDateToApi, formatDisplayDate } from './utils';

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

const sortOptions = [
  { value: 'cost', label: 'Сначала дешевле' },
  { value: 'duration', label: 'Сначала быстрее' },
  { value: 'transfers', label: 'Меньше пересадок' },
  { value: 'departure', label: 'По времени отправления' },
  { value: 'closest_time', label: 'Ближайшее время' },
];

const initialFilters = {
  max_transfers: 3,
  min_cost: '',
  max_cost: '',
  min_duration: '',
  max_duration: '',
};

export default function App() {
  const [cities, setCities] = useState([]);
  const [loadingCities, setLoadingCities] = useState(true);
  const [routeLoading, setRouteLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState(initialFilters);
  const [draftFilters, setDraftFilters] = useState(initialFilters);
  const [sortBy, setSortBy] = useState('cost');
  const [draftSortBy, setDraftSortBy] = useState('cost');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isSortOpen, setIsSortOpen] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [hoveredTransport, setHoveredTransport] = useState(null);
  const dateInputRef = useRef(null);

  const [form, setForm] = useState(() => ({
    origin: '',
    destination: '',
    date: '',
    transport: [],
  }));

  useEffect(() => {
    let mounted = true;
    getCities()
      .then((data) => {
        if (!mounted) return;
        setCities(data.cities || []);
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err.message);
      })
      .finally(() => {
        if (mounted) setLoadingCities(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const cityOptions = useMemo(() => cities.sort((a, b) => a.localeCompare(b, 'ru')), [cities]);

  async function handleSearch(event) {
    event?.preventDefault();
    setError('');
    setRouteLoading(true);

    const selectedTransport = form.transport.length === 1 ? form.transport[0] : undefined;

    try {
      const data = await getRoutes({
        origin: form.origin,
        destination: form.destination,
        date: uiDateToApi(form.date),
        sort_by: sortBy,
        sort_order: 'asc',
        transport: selectedTransport,
        max_transfers: filters.max_transfers,
        min_cost: filters.min_cost,
        max_cost: filters.max_cost,
        min_duration: filters.min_duration,
        max_duration: filters.max_duration,
      });

      const routes = (data.routes || []).map((route) => ({
        ...route,
        origin: data.origin,
        destination: data.destination,
      }));

      setSearchResult({ ...data, routes });
    } catch (err) {
      setSearchResult(null);
      setError(err.message);
    } finally {
      setRouteLoading(false);
    }
  }

  function updateForm(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function toggleTransport(type) {
    setForm((current) => {
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

  function openDatePicker() {
    const input = dateInputRef.current;
    if (!input) return;

    input.focus();
    if (typeof input.showPicker === 'function') {
      input.showPicker();
      return;
    }
    input.click();
  }

  useEffect(() => {
    if (searchResult) {
      handleSearch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, sortBy]);

  const activeSortLabel = sortOptions.find((item) => item.value === sortBy)?.label || 'Сортировка';
  const dateLabel = formatDisplayDate(searchResult?.date || form.date);

  return (
    <div className="page-shell">
      <header className="topbar">
        <img src={logo} alt="Т-Путешествия" className="topbar__logo" />
      </header>

      <main className={`page-content ${searchResult ? 'page-content--results' : ''}`}>
        {!searchResult && (
          <section className="hero">
            <h1>Т-Путешествия</h1>

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
                    />
                  </div>

                  <label className="field field--with-icon field--date">
                    <input
                      ref={dateInputRef}
                      type="date"
                      className="date-input date-input--empty"
                      value={form.date}
                      onChange={(event) => updateForm('date', event.target.value)}
                      aria-label="Дата отправления"
                    />
                    <span className={`field-placeholder ${form.date ? 'field-placeholder--filled' : ''}`}>
                      {form.date ? formatDisplayDate(form.date) : 'Дата отправления'}
                    </span>
                    <button
                      type="button"
                      className="calendar-trigger"
                      aria-label="Открыть календарь"
                      onClick={openDatePicker}
                    >
                      <img src={calendarIcon} alt="" />
                    </button>
                  </label>
                </div>

                <div className="search-card__mediaside">
                  {transportTiles.map((tile) => {
                    const isSelected = form.transport.includes(tile.key);
                    const isHovered = hoveredTransport === tile.key;

                    return (
                      <button
                        key={tile.key}
                        type="button"
                        className={`transport-tile ${isSelected ? 'is-selected' : ''} ${isHovered ? 'is-hovered' : ''}`}
                        onMouseEnter={() => setHoveredTransport(tile.key)}
                        onMouseLeave={() => setHoveredTransport(null)}
                        onFocus={() => setHoveredTransport(tile.key)}
                        onBlur={() => setHoveredTransport(null)}
                        onClick={() => toggleTransport(tile.key)}
                        aria-pressed={isSelected}
                      >
                        <img src={tile.image} alt={tile.label} />
                        <span>{tile.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <button
                className="search-button"
                type="submit"
                disabled={routeLoading || loadingCities}
              >
                {routeLoading ? 'Ищем…' : 'Найти'}
              </button>
            </form>

            <datalist id="cities-list">
              {cityOptions.map((city) => (
                <option value={city} key={city} />
              ))}
            </datalist>

            {error && <div className="message message--error">{error}</div>}
          </section>
        )}

        {searchResult && (
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
                  {searchResult.count} {searchResult.count === 1 ? 'маршрут' : searchResult.count < 5 ? 'маршрута' : 'маршрутов'}
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
                <h2>Маршруты не найдены</h2>
                <p>Попробуйте изменить дату, тип транспорта или фильтры.</p>
              </div>
            )}

            <div className="tickets-grid">
              {searchResult.routes.map((route, index) => (
                <TicketCard key={`${route.departure}-${route.arrival}-${index}`} route={route} />
              ))}
            </div>
          </section>
        )}
      </main>

      <Modal title="Сортировка" isOpen={isSortOpen} onClose={() => setIsSortOpen(false)}>
        <div className="option-list">
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
        <button className="modal-apply" onClick={applySort}>Применить</button>
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
