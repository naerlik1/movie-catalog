export class ApiError extends Error {
  constructor(status, errors) {
    super(errors.non_field_errors || Object.values(errors)[0] || 'Не удалось выполнить запрос');
    this.status = status;
    this.errors = errors;
  }
}

export async function api(path, { body, binary = false, ...options } = {}) {
  const token = sessionStorage.getItem('access');
  const headers = { ...options.headers };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(`/api${path}`, { ...options, headers, body });
  } catch {
    throw new ApiError(0, { non_field_errors: 'Нет связи с сервером. Попробуйте ещё раз.' });
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    if (response.status === 401 && token) {
      sessionStorage.removeItem('access');
      window.dispatchEvent(new Event('auth-expired'));
    }
    throw new ApiError(response.status, data.errors || { non_field_errors: 'Не удалось выполнить запрос' });
  }
  if (response.status === 204) return null;
  if (binary) return { blob: await response.blob(), filename: response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] || 'movies.xlsx' };
  return response.json();
}
