const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';
const CLIENT_TIMEZONE = Intl.DateTimeFormat().resolvedOptions().timeZone || '';

async function request(path, { params, method = 'GET', body } = {}) {
  const url = new URL(path, API_BASE);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        return;
      }

      if (Array.isArray(value)) {
        if (value.length > 0) {
          url.searchParams.set(key, value.join(','));
        }
        return;
      }

      url.searchParams.set(key, value);
    });
  }

  const headers = {};
  if (CLIENT_TIMEZONE) {
    headers['X-Client-Timezone'] = CLIENT_TIMEZONE;
  }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url.toString(), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Ошибка запроса к серверу');
  }

  return data;
}

export function getCities() {
  return request('/cities');
}

export function getClientContext() {
  return request('/client-context');
}

export function getRoutes(params) {
  return request('/routes', { params });
}

export function getFlightsFromCity(city) {
  return request(`/flights/${encodeURIComponent(city)}`);
}

export function getItinerary(payload) {
  return request('/itinerary', { method: 'POST', body: payload });
}
