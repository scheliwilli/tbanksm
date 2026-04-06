import { formatDuration, formatPrice, getTransportBadge } from '../utils';
import CarrierLink from './CarrierLink';
import HighlightFlags from './HighlightFlags';

function FlightRow({ flight }) {
  const isFeatured = flight.isCheapest || flight.isFastest;

  return (
    <article className={`flight-row ${isFeatured ? 'is-featured' : ''}`}>
      <div className="flight-row__head">
        <div>
          <div className="flight-row__eyebrow">{getTransportBadge(flight.transport)}</div>
          <h3>{flight.from} → {flight.to}</h3>
        </div>
        <div className="flight-row__price">от {formatPrice(flight.cost)}</div>
      </div>

      <div className="flight-row__timeline">
        <div>
          <span>Отправление</span>
          <strong>{flight.departure}</strong>
        </div>
        <div>
          <span>Прибытие</span>
          <strong>{flight.arrival}</strong>
        </div>
        <div>
          <span>В пути</span>
          <strong>{formatDuration(flight.duration_min)}</strong>
        </div>
      </div>

      {(flight.carrier || flight.id) && (
        <div className="flight-row__meta">
          {flight.carrier && <CarrierLink name={flight.carrier} url={flight.carrier_url} />}
          {flight.id && <span>Рейс {flight.id}</span>}
        </div>
      )}

      <HighlightFlags
        isCheapest={flight.isCheapest}
        isFastest={flight.isFastest}
        className="flight-row__flags"
      />
    </article>
  );
}

export default function FlightCatalog({ catalog, isOpen, onToggle }) {
  return (
    <section className={`destination-catalog ${isOpen ? 'is-open' : ''}`}>
      <button
        type="button"
        className="destination-catalog__trigger"
        onClick={onToggle}
        aria-expanded={isOpen}
      >
        <div className="destination-catalog__intro">
          <span className="destination-catalog__eyebrow">Направление</span>
          <strong className="destination-catalog__title">{catalog.destination}</strong>

          <div className="destination-catalog__summary">
            <span>{catalog.countLabel}</span>
            <span>от {formatPrice(catalog.cheapestCost)}</span>
            <span>от {formatDuration(catalog.fastestDuration)}</span>
            {catalog.highlightedCount > 0 && <span>с флажками: {catalog.highlightedCount}</span>}
          </div>
        </div>

        <span className="destination-catalog__toggle">
          {isOpen ? 'Скрыть рейсы' : 'Показать рейсы'}
        </span>
      </button>

      {isOpen && (
        <div className="destination-catalog__content">
          {catalog.flights.map((flight, index) => (
            <FlightRow
              key={`${catalog.destination}-${flight.departure_iso}-${flight.id || index}`}
              flight={flight}
            />
          ))}
        </div>
      )}
    </section>
  );
}
