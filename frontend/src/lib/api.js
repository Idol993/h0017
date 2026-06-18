import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

export const getDecks = () => api.get('/api/decks').then(res => res.data);
export const createDeck = (data) => api.post('/api/decks', data).then(res => res.data);
export const updateDeck = (id, data) => api.put(`/api/decks/${id}`, data).then(res => res.data);
export const deleteDeck = (id) => api.delete(`/api/decks/${id}`).then(res => res.data);

export const getCards = (deckId) => api.get('/api/cards', { params: { deck_id: deckId } }).then(res => res.data);
export const createCard = (deckId, data) => api.post('/api/cards', { ...data, deck_id: deckId }).then(res => res.data);
export const updateCard = (deckId, cardId, data) => api.put(`/api/cards/${cardId}`, data).then(res => res.data);
export const deleteCard = (deckId, cardId) => api.delete(`/api/cards/${cardId}`).then(res => res.data);

export const getTodayCards = () => api.get('/api/today').then(res => res.data);
export const submitReview = (cardId, rating, durationSeconds = 0) => api.post(`/api/review/${cardId}`, { rating, duration_seconds: durationSeconds }).then(res => res.data);

export const importCSV = (deckId, formData) => api.post(`/api/import/csv?deck_id=${deckId}`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
}).then(res => res.data);

export const getStats = () => api.get('/api/stats').then(res => res.data);

export const exportJSON = () => api.get('/api/export/json').then(res => res.data);
export const importJSON = (formData) => api.post('/api/import/json', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
}).then(res => res.data);

export default api;
