import { formatDuration, formatPrice, formatTransfers, getTransportBadge, getTransportLabel } from '../utils';
import CarrierLink from './CarrierLink';
import HighlightFlags from './HighlightFlags';

function SegmentRow({ segment, isLast }) {
  return (
    <div className="segment-row">
      <div className="segment-times">
        <strong>{segment.departure.slice(11)}</strong>
        <span>{segment.departure.slice(0, 10)}</span>
      </div>
      <div className="segment-visual">
        <span className="segment-dot" />
        {!isLast && <span className="segment-line" />}
      </div>
      <div className="segment-details">
        <div className="segment-route">
          <strong>{segment.from}</strong>
          <span>{segment.to}</span>
        </div>
        <div className="segment-meta">
          <span className="segment-badge">{getTransportBadge(segment.transport)}</span>
          <span>{formatDuration(segment.duration_min)}</span>
          <span>Прибытие {segment.arrival.slice(11)}</span>
          {segment.carrier && <CarrierLink name={segment.carrier} url={segment.carrier_url} />}
        </div>
      </div>
    </div>
  );
}

export default function TicketCard({ route }) {
  const transportKinds = Array.from(new Set(route.segments.map((segment) => segment.transport)));
  const primaryTransport = transportKinds.length === 1 ? transportKinds[0] : undefined;
  const isFeatured = route.isCheapest || route.isFastest;

  return (
    <article className={`ticket-card ${isFeatured ? 'is-featured' : ''}`}>
      <div className="ticket-card__top">
        <div>
          <div className="ticket-card__eyebrow">{primaryTransport ? getTransportLabel(primaryTransport) : 'Смешанный маршрут'}</div>
          <h3>
            {route.origin || route.segments[0]?.from} → {route.destination || route.segments.at(-1)?.to}
          </h3>
        </div>
        <div className="ticket-card__price">от {formatPrice(route.total_cost)}</div>
      </div>

      <div className="ticket-card__summary">
        <div>
          <span>Отправление</span>
          <strong>{route.departure}</strong>
        </div>
        <div>
          <span>Прибытие</span>
          <strong>{route.arrival}</strong>
        </div>
        <div>
          <span>В пути</span>
          <strong>{formatDuration(route.total_duration_min)}</strong>
        </div>
        <div>
          <span>Пересадки</span>
          <strong>{formatTransfers(route.transfers)}</strong>
        </div>
      </div>

      <HighlightFlags
        isCheapest={route.isCheapest}
        isFastest={route.isFastest}
        className="ticket-card__flags"
      />

      <div className="ticket-card__segments">
        {route.segments.map((segment, index) => (
          <SegmentRow
            key={`${segment.id || segment.departure_iso || segment.departure}-${index}`}
            segment={segment}
            isLast={index === route.segments.length - 1}
          />
        ))}
      </div>
    </article>
  );
}
