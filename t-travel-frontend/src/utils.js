export function formatPrice(value) {
  return new Intl.NumberFormat('ru-RU').format(value) + ' ₽';
}

export function formatDuration(totalMinutes) {
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;  

  const parts = [];
  if (days) parts.push(`${days} д`);
  if (hours) parts.push(`${hours} ч`);
  if (minutes || parts.length === 0) parts.push(`${minutes} мин`);
  return parts.join(' ');
}

export function formatTransfers(count) {
  if (count === 0) return 'Без пересадок';
  if (count === 1) return '1 пересадка';
  if (count < 5) return `${count} пересадки`;
  return `${count} пересадок`;
}

export function normalizeDateValue(value) {
  if (!value) return '';
  return value;
}

export function uiDateToApi(value) {
  if (!value) return '';
  const parts = value.split('-');
  if (parts.length === 3) {
    return `${parts[2]}.${parts[1]}.${parts[0]}`;
  }
  return value;
}

export function apiDateToUi(value) {
  if (!value) return '';
  const parts = value.split('.');
  if (parts.length === 3) {
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }
  return value;
}

export function formatDisplayDate(value) {
  if (!value) return '';
  if (value.includes('-')) {
    const parts = value.split('-');
    if (parts.length === 3) {
      return `${parts[2]}.${parts[1]}.${parts[0].slice(-2)}`;
    }
  } else if (value.includes('.')) {
    const parts = value.split('.');
    if (parts.length === 3 && parts[2].length === 4) {
      return `${parts[0]}.${parts[1]}.${parts[2].slice(-2)}`;
    }
  }
  return value;
}

export function getTransportLabel(transport) {
  switch (transport) {
    case 'plane':
      return 'Авиабилет';
    case 'train':
      return 'Ж/д билет';
    case 'bus':
      return 'Автобус';
    case 'electrictrain':
      return 'Электричка';
    default:
      return 'Маршрут';
  }
}

export function getTransportBadge(transport) {
  switch (transport) {
    case 'plane':
      return 'Самолет';
    case 'train':
      return 'Поезд';
    case 'bus':
      return 'Автобус';
    case 'electrictrain':
      return 'Электричка';
    default:
      return 'Транспорт';
  }
}

export function formatStayHours(hours) {
  if (!hours) return '0 ч';
  if (hours < 24) return `${hours} ч`;

  const days = Math.floor(hours / 24);
  const restHours = hours % 24;
  const parts = [`${days} д`];
  if (restHours) parts.push(`${restHours} ч`);
  return parts.join(' ');
}

export function formatClientLocation(clientContext) {
  if (!clientContext) return '';
  const city = clientContext.city || clientContext.region;
  if (city && clientContext.timezone) {
    return `${city} · ${clientContext.timezone}`;
  }
  if (city) return city;
  return clientContext.timezone || '';
}
