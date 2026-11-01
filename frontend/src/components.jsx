import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from './auth';

export function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  async function exit() {
    setBusy(true); setError('');
    try { await logout(); navigate('/login'); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  return <>
    <header className="header"><div className="header-inner">
      <Link className="brand" to="/"><span className="brand-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4" /></svg></span> Каталог фильмов</Link>
      <nav aria-label="Основная навигация">
        <NavLink to="/" end>Каталог</NavLink>
        {user && <NavLink to="/favorites">Избранное</NavLink>}
      </nav>
      <div className="account">{user ? <><span className="username">{user.username}<small>{user.role === 'admin' ? 'Администратор' : 'Пользователь'}</small></span><button className="header-button" onClick={exit} disabled={busy}>{busy ? 'Выход…' : 'Выйти'}</button></> : <><Link to="/login">Войти</Link><Link className="header-button" to="/register">Регистрация</Link></>}</div>
    </div></header>
    <main className="container">{error && <ErrorMessage>{error}</ErrorMessage>}{children}</main>
    <footer>Каталог фильмов <span>Учебная практика · Вариант 25</span></footer>
  </>;
}

export function ErrorMessage({ children }) { return children ? <div className="error-message" role="alert">{children}</div> : null; }
export function FieldError({ error, id }) { return error ? <span className="field-error" id={id}>{error}</span> : null; }
export function Loading() { return <div className="status" role="status">Загрузка…</div>; }
export function Rating({ value, count }) { return <span className="rating"><span aria-hidden="true">★</span> {value == null ? 'Нет оценок' : Number(value).toFixed(1)}{count !== undefined && <small>{value == null ? ' · ' : ' / 10 · '}Отзывов: {count}</small>}</span>; }

export function Poster({ movie, large = false }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [movie.poster?.url]);
  return <div className={`poster ${large ? 'poster-large' : ''}`}>
    {movie.poster && !failed ? <img src={movie.poster.url} alt={`Постер фильма «${movie.title}»`} onError={() => setFailed(true)} /> : <div className="poster-placeholder"><span aria-hidden="true">▶</span><span>{movie.title}</span><small>{movie.year} · Без постера</small></div>}
  </div>;
}

export function Pagination({ page, count, size = 12, onChange }) {
  const pages = Math.ceil(count / size);
  if (pages <= 1) return null;
  return <nav className="pagination" aria-label="Пагинация"><button className="secondary" onClick={() => onChange(page - 1)} disabled={page <= 1}>← Назад</button><span>Страница {page} из {pages}</span><button className="secondary" onClick={() => onChange(page + 1)} disabled={page >= pages}>Далее →</button></nav>;
}

export function ConfirmDialog({ title, children, onConfirm, onClose, busy }) {
  const cancelRef = useRef(null);
  const dialogRef = useRef(null);
  useEffect(() => {
    const previous = document.activeElement;
    cancelRef.current?.focus();
    function keydown(event) {
      if (event.key === 'Escape' && !busy) onClose();
      if (event.key === 'Tab') {
        const buttons = dialogRef.current?.querySelectorAll('button:not(:disabled)');
        if (!buttons?.length) return;
        const first = buttons[0], last = buttons[buttons.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    }
    document.addEventListener('keydown', keydown);
    return () => { document.removeEventListener('keydown', keydown); previous?.focus(); };
  }, [busy, onClose]);
  return <div className="modal-overlay"><section className="modal" ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="confirm-title"><h2 id="confirm-title">{title}</h2>{children}<div className="actions"><button ref={cancelRef} className="secondary" disabled={busy} onClick={onClose}>Отмена</button><button className="danger" disabled={busy} onClick={onConfirm}>{busy ? 'Удаление…' : 'Удалить'}</button></div></section></div>;
}
