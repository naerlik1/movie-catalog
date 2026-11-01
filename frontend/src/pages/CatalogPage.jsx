import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { ErrorMessage, Loading, Pagination, Poster, Rating } from '../components';

export default function CatalogPage({ favorites = false }) {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const isAdmin = user?.role === 'admin';
  const scope = favorites ? 'favorites' : isAdmin ? params.get('scope') || 'all' : 'all';
  const appliedSearch = params.get('search') || '';
  const appliedYear = params.get('year') || '';
  const appliedRating = params.get('rating_min') || '';
  const appliedOrdering = params.get('ordering') || 'newest';
  const page = Math.max(1, Number(params.get('page')) || 1);
  const [form, setForm] = useState({ search: params.get('search') || '', year: params.get('year') || '', rating_min: params.get('rating_min') || '', ordering: params.get('ordering') || 'newest' });
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [exportError, setExportError] = useState('');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [retry, setRetry] = useState(0);
  const query = new URLSearchParams(params);
  query.set('scope', scope);
  query.set('limit', '12');
  const queryString = query.toString();
  const searchPending = form.search !== appliedSearch;

  useEffect(() => {
    setForm(current => ({ ...current, search: appliedSearch }));
  }, [appliedSearch]);
  useEffect(() => {
    setForm(current => ({ ...current, year: appliedYear, rating_min: appliedRating, ordering: appliedOrdering }));
  }, [appliedYear, appliedRating, appliedOrdering]);
  useEffect(() => {
    if (form.search === appliedSearch) return;
    const timer = setTimeout(() => {
      const next = new URLSearchParams(params);
      if (form.search) next.set('search', form.search);
      else next.delete('search');
      next.delete('page');
      setParams(next, { replace: true });
    }, 300);
    return () => clearTimeout(timer);
  }, [form.search, appliedSearch, params, setParams]);
  useEffect(() => {
    let active = true;
    setLoading(true); setError(''); setExportError('');
    api(`/movies?${queryString}`).then(result => { if (active) setData(result); })
      .catch(err => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [queryString, retry, user?.id]);

  function apply(event) {
    event.preventDefault();
    const next = new URLSearchParams();
    Object.entries(form).forEach(([key, value]) => { if (value.trim()) next.set(key, value.trim()); });
    if (!favorites) next.set('scope', scope);
    setParams(next);
  }
  function changeScope(value) { const next = new URLSearchParams(params); next.set('scope', value); next.delete('page'); setParams(next); }
  async function download() {
    setExporting(true); setExportError('');
    try {
      const result = await api(`/movies/export/?${queryString}`, { binary: true });
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement('a'); link.href = url; link.download = result.filename; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) { setExportError(err.message); }
    finally { setExporting(false); }
  }
  return <>
    <div className="page-heading catalog-heading"><div><div className="eyebrow">{favorites ? 'Ваша коллекция' : 'Найдите кино на вечер'}</div><h1>{favorites ? 'Избранное' : 'Каталог фильмов'}</h1><p className="muted">{favorites ? 'Фильмы, к которым хочется вернуться.' : 'Выбирайте фильмы, смотрите оценки и делитесь отзывами.'}</p></div>
      <div className="actions">{user && (isAdmin || favorites) && <button className="secondary" onClick={download} disabled={loading || exporting || searchPending}>{exporting ? 'Подготовка…' : 'Скачать Excel'}</button>}{isAdmin && <Link className="button" to="/items/new">+ Добавить фильм</Link>}</div>
    </div>
    {!favorites && isAdmin && <div className="tabs" aria-label="Раздел каталога"><button className={scope === 'all' ? 'selected' : ''} onClick={() => changeScope('all')}>Все фильмы</button><button className={scope === 'mine' ? 'selected' : ''} onClick={() => changeScope('mine')}>Мои записи</button></div>}
    <form className="filters" onSubmit={apply}>
      <label className="search-field">Поиск<input name="search" placeholder="Название или описание" value={form.search} maxLength={120} onChange={e => setForm({ ...form, search: e.target.value })} /></label>
      <label>Год<input name="year" type="number" placeholder="Любой" min="1888" max="9999" value={form.year} onChange={e => setForm({ ...form, year: e.target.value })} /></label>
      <label>Рейтинг от<select name="rating_min" value={form.rating_min} onChange={e => setForm({ ...form, rating_min: e.target.value })}><option value="">Любой</option>{[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(v => <option key={v} value={v}>{v}</option>)}</select></label>
      <label>Сортировка<select name="ordering" value={form.ordering} onChange={e => setForm({ ...form, ordering: e.target.value })}><option value="newest">Сначала новые</option><option value="rating">По рейтингу</option><option value="year">По году</option><option value="title">По названию</option></select></label>
      <button type="submit">Найти</button><button type="button" className="link-button" onClick={() => { setForm({ search: '', year: '', rating_min: '', ordering: 'newest' }); setParams(scope !== 'all' && !favorites ? { scope } : {}); }}>Сбросить</button>
    </form>
    <ErrorMessage>{exportError}</ErrorMessage>
    {loading ? <Loading /> : error ? <div className="empty"><ErrorMessage>{error}</ErrorMessage><button onClick={() => setRetry(v => v + 1)}>Повторить</button></div> : <>
      <div className="results-line"><span role="status">{searchPending ? 'Поиск…' : <>Найдено фильмов: <strong>{data?.count || 0}</strong></>}</span>{!user && <span><Link to="/login">Войдите</Link>, чтобы оставлять отзывы</span>}</div>
      {data?.results.length ? <div className="movie-grid">{data.results.map(movie => <article className="movie-card" key={movie.id}><Link className="card-link" to={`/items/${movie.id}`}><Poster movie={movie} /><div className="card-body"><div className="card-meta"><span className={movie.is_watched ? 'watched-label' : ''}>{movie.year}{movie.is_watched && ' · Просмотрен'}</span>{movie.is_favorite && <span className="favorite-label">♥ В избранном</span>}</div><h2>{movie.title}</h2><Rating value={movie.average_rating} /><p>{movie.description || 'Описание пока не добавлено.'}</p></div></Link></article>)}</div> : <div className="empty"><div className="empty-icon" aria-hidden="true">◇</div><h2>{favorites ? 'Здесь пока пусто' : 'Фильмы не найдены'}</h2><p>{favorites ? 'Откройте карточку фильма и добавьте его в избранное.' : scope === 'mine' ? 'В этом разделе фильмы, которые добавили вы. Добавлять фильмы может только администратор.' : 'Попробуйте изменить поиск или сбросить фильтры.'}</p><Link to="/">Открыть каталог</Link></div>}
      <Pagination page={page} count={data?.count || 0} onChange={value => { const next = new URLSearchParams(params); next.set('page', value); setParams(next); window.scrollTo({ top: 0, behavior: 'smooth' }); }} />
    </>}
  </>;
}
