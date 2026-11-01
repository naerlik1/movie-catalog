import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { ErrorMessage, FieldError } from '../components';
import { validateAuth } from '../validation';

export default function AuthPage({ register = false }) {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [values, setValues] = useState({ username: '', email: '', password: '', password_confirm: '' });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/" replace />;
  const change = (event) => setValues({ ...values, [event.target.name]: event.target.value });
  async function submit(event) {
    event.preventDefault();
    const validation = validateAuth(values, register);
    setErrors(validation);
    if (Object.keys(validation).length) return;
    setBusy(true);
    try {
      if (register) {
        await api('/auth/register', { method: 'POST', body: values });
        navigate('/login', { replace: true, state: { registered: true } });
      } else {
        await login({ email: values.email, password: values.password });
        navigate(location.state?.from || '/', { replace: true });
      }
    } catch (err) { setErrors(err.errors || { non_field_errors: err.message }); }
    finally { setBusy(false); }
  }
  return <section className="auth-panel">
    <div className="eyebrow">Каталог фильмов</div><h1>{register ? 'Создать аккаунт' : 'С возвращением'}</h1>
    <p className="muted">{register ? 'Сохраняйте любимые фильмы и делитесь впечатлениями.' : 'Войдите, чтобы открыть избранное и оставить отзыв.'}</p>
    {location.state?.registered && !register && <p className="success" role="status">Аккаунт создан. Войдите с вашим email и паролем.</p>}
    <ErrorMessage>{errors.non_field_errors}</ErrorMessage>
    <form onSubmit={submit} noValidate>
      {register && <label>Логин<input name="username" value={values.username} onChange={change} autoComplete="username" maxLength={30} aria-invalid={!!errors.username} aria-describedby="username-error" /><FieldError id="username-error" error={errors.username} /></label>}
      <label>Email<input name="email" type="email" value={values.email} onChange={change} autoComplete="email" maxLength={254} aria-invalid={!!errors.email} aria-describedby="email-error" /><FieldError id="email-error" error={errors.email} /></label>
      <label>Пароль<input name="password" type="password" value={values.password} onChange={change} autoComplete={register ? 'new-password' : 'current-password'} aria-invalid={!!errors.password} aria-describedby="password-error" /><FieldError id="password-error" error={errors.password} />{register && <small>8–64 символа, минимум одна буква и одна цифра.</small>}</label>
      {register && <label>Повторите пароль<input name="password_confirm" type="password" value={values.password_confirm} onChange={change} autoComplete="new-password" aria-invalid={!!errors.password_confirm} aria-describedby="confirm-error" /><FieldError id="confirm-error" error={errors.password_confirm} /></label>}
      <button className="full-width" disabled={busy}>{busy ? 'Подождите…' : register ? 'Зарегистрироваться' : 'Войти'}</button>
    </form>
    <p className="auth-link">{register ? 'Уже есть аккаунт?' : 'Нет аккаунта?'} <Link to={register ? '/login' : '/register'}>{register ? 'Войти' : 'Зарегистрироваться'}</Link></p>
  </section>;
}
