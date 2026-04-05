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
    case 'electrictrain':
      return 'Электричка';
    default:
      return 'Транспорт';
  }
}
