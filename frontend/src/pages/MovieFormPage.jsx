import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api';
import { ErrorMessage, FieldError, Loading, Poster } from '../components';
import { validateMovie, validatePoster } from '../validation';

export default function MovieFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [values, setValues] = useState({ title: '', year: '', description: '' });
  const [movie, setMovie] = useState(null);
  const [file, setFile] = useState(null);
  const [createdId, setCreatedId] = useState(null);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(!!id);
  const [loadError, setLoadError] = useState('');
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!id) return;
    let active = true;
    setLoading(true); setLoadError('');
    api(`/movies/${id}`).then(result => {
      if (!active) return;
      if (!result.can_edit) { setLoadError('Редактировать фильм может только добавивший его администратор.'); return; }
      setMovie(result); setValues({ title: result.title, year: String(result.year), description: result.description });
    }).catch(err => { if (active) setLoadError(err.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id, retry]);
  async function submit(event) {
    event.preventDefault();
    const validation = validateMovie(values);
    const fileError = validatePoster(file);
    if (fileError) validation.file = fileError;
    setErrors(validation);
    if (Object.keys(validation).length) return;
    setBusy(true);
    let savedId = id || createdId;
    let saved = false;
    try {
      const body = { ...values, title: values.title.trim(), year: Number(values.year) };
      const result = await api(savedId ? `/movies/${savedId}` : '/movies', { method: savedId ? 'PUT' : 'POST', body });
      savedId = result.id;
      saved = true;
      setCreatedId(result.id);
      if (file) {
        const formData = new FormData(); formData.append('file', file);
        await api(`/movies/${result.id}/files`, { method: 'POST', body: formData });
      }
      navigate(`/items/${result.id}`);
    } catch (err) {
      const errorFields = err.errors || { non_field_errors: err.message };
      setErrors(saved && file ? { ...errorFields, non_field_errors: 'Фильм сохранён, но постер не загружен. Исправьте файл и повторите сохранение.' } : errorFields);
    } finally { setBusy(false); }
  }
  if (loading) return <Loading />;
  if (loadError) return <div className="empty"><ErrorMessage>{loadError}</ErrorMessage><button onClick={() => setRetry(v => v + 1)}>Повторить</button></div>;
  return <div className="form-page"><Link className="back-link" to={id ? `/items/${id}` : '/'}>← Назад</Link><h1>{id ? 'Редактировать фильм' : 'Новый фильм'}</h1><p className="muted">Название и год обязательны. Постер можно добавить позже.</p>
    <form className="panel movie-form" onSubmit={submit} noValidate>
      <ErrorMessage>{errors.non_field_errors}</ErrorMessage>
      <label>Название<input name="title" value={values.title} maxLength={120} onChange={e => setValues({ ...values, title: e.target.value })} aria-invalid={!!errors.title} /><FieldError error={errors.title} /></label>
      <label>Год выпуска<input name="year" type="number" min="1888" max={new Date().getFullYear()} value={values.year} onChange={e => setValues({ ...values, year: e.target.value })} aria-invalid={!!errors.year} /><FieldError error={errors.year} /></label>
      <label>Описание<textarea name="description" rows={6} value={values.description} maxLength={2000} onChange={e => setValues({ ...values, description: e.target.value })} aria-invalid={!!errors.description} /><span className="input-help">{values.description.length} / 2000</span><FieldError error={errors.description} /></label>
      {movie?.poster && <div className="existing-poster"><Poster movie={movie} /><span>Текущий постер: {movie.poster.original_name}<small>Новый файл заменит его после сохранения.</small></span></div>}
      <label>Постер<input name="file" type="file" accept=".jpg,.jpeg,.png,.webp" onChange={e => { const next = e.target.files[0] || null; setFile(next); setErrors({ ...errors, file: validatePoster(next) }); }} /><small>JPG, PNG или WEBP, до 5 МБ.</small><FieldError error={errors.file} /></label>
      <div className="actions"><button disabled={busy}>{busy ? 'Сохранение…' : 'Сохранить фильм'}</button><Link className="button secondary" to={createdId ? `/items/${createdId}` : id ? `/items/${id}` : '/'}>Отмена</Link></div>
    </form>
  </div>;
}
