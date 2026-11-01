export function validateAuth(values, register) {
  const errors = {};
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim()) || values.email.length > 254) errors.email = 'Введите корректный email';
  if (!values.password) errors.password = 'Введите пароль';
  if (register) {
    if (!/^[A-Za-z0-9_]{3,30}$/.test(values.username)) errors.username = 'Только латиница, цифры и _, от 3 до 30 символов';
    if (values.password.length < 8 || values.password.length > 64 || !/[A-Za-zА-Яа-яЁё]/.test(values.password) || !/[0-9]/.test(values.password)) errors.password = 'Пароль: от 8 до 64 символов, буквы и цифры';
    if (values.password_confirm !== values.password) errors.password_confirm = 'Пароли не совпадают';
  }
  return errors;
}

export function validateMovie(values) {
  const errors = {};
  if (!values.title.trim() || values.title.trim().length > 120) errors.title = 'Введите название (до 120 символов)';
  const year = Number(values.year);
  if (!Number.isInteger(year) || year < 1888 || year > new Date().getFullYear()) errors.year = `Год должен быть от 1888 до ${new Date().getFullYear()}`;
  if (values.description.length > 2000) errors.description = 'Не более 2000 символов';
  return errors;
}

export function validatePoster(file) {
  if (!file) return '';
  if (file.size > 5 * 1024 * 1024) return 'Размер постера не должен превышать 5 МБ';
  if (!/\.(jpe?g|png|webp)$/i.test(file.name) || !['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) return 'Разрешены только JPG, PNG и WEBP';
  return '';
}
