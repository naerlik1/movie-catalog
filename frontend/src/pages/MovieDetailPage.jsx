import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { ConfirmDialog, ErrorMessage, FieldError, Loading, Pagination, Poster, Rating } from '../components';

export default function MovieDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [movie, setMovie] = useState(null);
  const [reviews, setReviews] = useState(null);
  const [myReview, setMyReview] = useState(null);
  const [values, setValues] = useState({ rating: '', text: '' });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [errors, setErrors] = useState({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState(false);
  const [favoriteBusy, setFavoriteBusy] = useState(false);
  const [watchedBusy, setWatchedBusy] = useState(false);
  const [dialog, setDialog] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => { setPage(1); }, [id]);
  useEffect(() => {
    let active = true;
    setLoading(true); setLoadError('');
    Promise.all([api(`/movies/${id}`), api(`/movies/${id}/reviews?page=${page}`), user ? api(`/movies/${id}/my-review`) : Promise.resolve(null)])
      .then(([film, list, own]) => {
        if (!active) return;
        setMovie(film); setReviews(list); setMyReview(own);
        setValues(own ? { rating: String(own.rating), text: own.text } : { rating: '', text: '' });
      }).catch(err => { if (active) setLoadError(err.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id, page, revision, user?.id]);
  async function toggleFavorite() {
    setFavoriteBusy(true); setError('');
    try { await api(`/movies/${id}/favorite`, { method: movie.is_favorite ? 'DELETE' : 'POST' }); setMovie(current => ({ ...current, is_favorite: !movie.is_favorite })); }
    catch (err) { setError(err.message); }
    finally { setFavoriteBusy(false); }
  }
  async function toggleWatched() {
    setWatchedBusy(true); setError('');
    try {
      await api(`/movies/${id}/watched`, { method: movie.is_watched ? 'DELETE' : 'POST' });
      setMovie(current => ({ ...current, is_watched: !movie.is_watched }));
    } catch (err) { setError(err.message); }
    finally { setWatchedBusy(false); }
  }
  async function saveReview(event) {
    event.preventDefault();
    if (!movie.is_watched) {
      setErrors({ non_field_errors: 'Сначала отметьте фильм как просмотренный.' });
      return;
    }
    const validation = {};
    const rating = Number(values.rating);
    if (!Number.isInteger(rating) || rating < 1 || rating > 10) validation.rating = 'Выберите оценку от 1 до 10';
    if (!values.text.trim()) validation.text = 'Напишите текст отзыва';
    if (values.text.length > 2000) validation.text = 'Не более 2000 символов';
    setErrors(validation); setSuccess('');
    if (Object.keys(validation).length) return;
    setBusy(true);
    try {
      await api(myReview ? `/reviews/${myReview.id}` : `/movies/${id}/reviews`, { method: myReview ? 'PUT' : 'POST', body: { rating, text: values.text.trim() } });
      setSuccess('Отзыв сохранён. Рейтинг обновлён.'); setRevision(v => v + 1);
    } catch (err) { setErrors(err.errors || { non_field_errors: err.message }); }
    finally { setBusy(false); }
  }
  async function confirmDelete() {
    setBusy(true); setError('');
    try {
      const path = dialog === 'movie' ? `/movies/${id}` : dialog === 'poster' ? `/files/${movie.poster.id}` : `/reviews/${myReview.id}`;
      await api(path, { method: 'DELETE' });
      if (dialog === 'movie') { navigate('/'); return; }
      if (dialog === 'review') { setSuccess('Отзыв удалён. Рейтинг обновлён.'); setErrors({}); }
      setDialog(''); setRevision(v => v + 1);
    } catch (err) { setError(err.message); setDialog(''); }
    finally { setBusy(false); }
  }
  if (loading) return <Loading />;
  if (loadError) return <div className="empty"><ErrorMessage>{loadError}</ErrorMessage><button onClick={() => setRevision(v => v + 1)}>Повторить</button><p><Link to="/">Вернуться в каталог</Link></p></div>;
  return <>
    <Link className="back-link" to="/">← В каталог</Link>
    <ErrorMessage>{error}</ErrorMessage>
    <section className="movie-detail"><div><Poster movie={movie} large />{movie.can_edit && movie.poster && <button className="link-button remove-poster" onClick={() => setDialog('poster')}>Удалить постер</button>}</div><div className="movie-info"><div className="eyebrow">Фильм · {movie.year}</div><h1>{movie.title}</h1><Rating value={movie.average_rating} count={movie.reviews_count} />
      <h2>О фильме</h2><p className="description">{movie.description || 'Описание пока не добавлено.'}</p>
      <div className="actions">{user ? <><button onClick={toggleFavorite} disabled={favoriteBusy} className={movie.is_favorite ? 'secondary' : ''}>{favoriteBusy ? 'Сохранение…' : movie.is_favorite ? '♥ Убрать из избранного' : '♡ В избранное'}</button><button className="secondary" onClick={toggleWatched} disabled={watchedBusy || (movie.is_watched && !!myReview)} title={myReview ? 'Чтобы снять отметку, сначала удалите свой отзыв.' : ''}>{watchedBusy ? 'Сохранение…' : movie.is_watched ? '✓ Просмотрен' : 'Отметить просмотренным'}</button></> : <Link className="button" to="/login" state={{ from: `/items/${id}` }}>Войти и оставить отзыв</Link>}{movie.can_edit && <><Link className="button secondary" to={`/items/${id}/edit`}>Редактировать</Link><button className="link-button danger-text" onClick={() => setDialog('movie')}>Удалить фильм</button></>}</div>
      {myReview && <p className="watch-help">Чтобы снять отметку просмотра, сначала удалите свой отзыв.</p>}
    </div></section>
    <section className="reviews-section"><div className="section-heading"><h2>Отзывы зрителей <span>{reviews?.count || 0}</span></h2><span className="muted">Одна оценка от каждого зрителя</span></div>
      <div className="reviews-layout"><div>
        {reviews?.results.length ? reviews.results.map(review => <article className="review" key={review.id}><div className="review-top"><strong>{review.username}{review.owner_id === user?.id && <small> · Вы</small>}</strong><span className="review-rating">{review.rating} / 10</span></div><time dateTime={review.created_at}>{new Date(review.created_at).toLocaleDateString('ru-RU')}</time><p>{review.text}</p></article>) : <div className="panel"><h3>Отзывов пока нет</h3><p className="muted">Будьте первым, кто поделится впечатлениями.</p></div>}
        <Pagination page={page} count={reviews?.count || 0} onChange={setPage} />
      </div><aside className="panel review-form"><h3>{myReview ? 'Ваш отзыв' : 'Поделитесь впечатлениями'}</h3>
        {user && movie.is_watched && <form onSubmit={saveReview} noValidate><p className="muted">{myReview ? 'Можно изменить оценку и текст или удалить отзыв.' : 'Оцените фильм от 1 до 10 и напишите пару слов.'}</p><ErrorMessage>{errors.non_field_errors}</ErrorMessage>{success && <p className="success" role="status">{success}</p>}
          <label>Ваша оценка<select name="rating" value={values.rating} onChange={e => setValues({ ...values, rating: e.target.value })} aria-invalid={!!errors.rating}><option value="">Выберите оценку</option>{Array.from({ length: 10 }, (_, i) => i + 1).map(value => <option value={value} key={value}>{value} / 10</option>)}</select><FieldError error={errors.rating} /></label>
          <label>Текст отзыва<textarea name="text" rows={5} maxLength={2000} value={values.text} onChange={e => setValues({ ...values, text: e.target.value })} aria-invalid={!!errors.text} /><span className="input-help">{values.text.length} / 2000</span><FieldError error={errors.text} /></label>
          <button disabled={busy}>{busy ? 'Сохранение…' : myReview ? 'Сохранить изменения' : 'Опубликовать отзыв'}</button>{myReview && <button type="button" className="link-button danger-text" onClick={() => setDialog('review')} disabled={busy}>Удалить мой отзыв</button>}
        </form>}
        {user && !movie.is_watched && <div className="watch-notice"><p>Оставить отзыв можно после просмотра фильма.</p><button className="secondary" onClick={toggleWatched} disabled={watchedBusy}>{watchedBusy ? 'Сохранение…' : 'Я посмотрел фильм'}</button></div>}
        {!user && <><p className="muted">Войдите в аккаунт, чтобы оставить отзыв и поставить оценку.</p><Link to="/login" state={{ from: `/items/${id}` }}>Войти</Link></>}
      </aside></div>
    </section>
    {dialog && <ConfirmDialog title={dialog === 'movie' ? 'Удалить фильм?' : dialog === 'poster' ? 'Удалить постер?' : 'Удалить ваш отзыв?'} onClose={() => setDialog('')} onConfirm={confirmDelete} busy={busy}><p>{dialog === 'movie' ? 'Фильм, постер, отзывы и отметки в избранном будут удалены без возможности восстановления.' : dialog === 'poster' ? 'Изображение будет удалено с сервера. Сам фильм останется.' : 'Текст и оценка будут удалены. Вы сможете оставить новый отзыв.'}</p></ConfirmDialog>}
  </>;
}
