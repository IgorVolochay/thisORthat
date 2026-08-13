import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { currentUser } from '../../services/auth';
import { api } from '../../services/api';
import './CreateCard.css';

const MAX_LENGTH = 150;

export default function CreateCard({ onBack }) {
  const { showToast, closeMenu } = useApp();
  const [choiceA, setChoiceA] = useState('');
  const [choiceB, setChoiceB] = useState('');
  const [isSending, setIsSending] = useState(false);

  const canSubmit = choiceA.trim().length > 0 && choiceB.trim().length > 0 && !isSending;

  async function handleSubmit() {
    if (!canSubmit) return;
    setIsSending(true);
    try {
      const result = await api.addCard(choiceA.trim(), choiceB.trim(), currentUser.id);
      if (!result.error) {
        showToast('Карточка отправлена на модерацию!');
        setTimeout(() => {
          closeMenu();
        }, 2000);
      } else {
        showToast('Ошибка: ' + (result.result || 'неизвестная'));
        setIsSending(false);
      }
    } catch (err) {
      console.error('Add card error:', err);
      showToast('Ошибка отправки');
      setIsSending(false);
    }
  }

  return (
    <div className="create-card custom-scroll">
      <button className="create-back" onClick={onBack} aria-label="Назад">
        ← Назад
      </button>

      <h2 className="create-title">Создать карточку</h2>

      <p className="create-rules">
        При создании карточек запрещается использование мата и ссылок.
        Все карточки проходят процесс модерации перед публикацией.
        Лимит по длине текста: {MAX_LENGTH} символов.
      </p>

      <div className="create-fields">
        <div className="create-field create-field--a">
          <textarea
            className="create-textarea"
            placeholder="Первый вариант"
            value={choiceA}
            onChange={(e) => setChoiceA(e.target.value.slice(0, MAX_LENGTH))}
            maxLength={MAX_LENGTH}
            rows={3}
          />
          <span className="create-counter">
            {choiceA.length}/{MAX_LENGTH}
          </span>
        </div>

        <div className="create-field create-field--b">
          <textarea
            className="create-textarea"
            placeholder="Второй вариант"
            value={choiceB}
            onChange={(e) => setChoiceB(e.target.value.slice(0, MAX_LENGTH))}
            maxLength={MAX_LENGTH}
            rows={3}
          />
          <span className="create-counter">
            {choiceB.length}/{MAX_LENGTH}
          </span>
        </div>
      </div>

      <button
        className={`create-submit ${canSubmit ? 'create-submit--active' : ''}`}
        onClick={handleSubmit}
        disabled={!canSubmit}
      >
        {isSending ? 'Отправка...' : 'Отправить!'}
      </button>
    </div>
  );
}
