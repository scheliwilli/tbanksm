const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

async function request(path, params) {
  const url = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, value);
      }
    });
  }

  const response = await fetch(url.toString());
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || 'Ошибка запроса к серверу');
  }

  return data;
}

export function getCities() {
  return request('/cities');
}

export function getRoutes(params) {
  return request('/routes', params);
}
