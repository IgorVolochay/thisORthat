import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { currentUser, hapticImpact, hapticNotification } from '../../services/auth';
import { api } from '../../services/api';
import './CreateCard.css';

const MAX_LENGTH = 150;

export default function CreateCard({ onBack }) {
  const { showToast, closeMenu, handleApiResponse } = useApp();
  const [choiceA, setChoiceA] = useState('');
  const [choiceB, setChoiceB] = useState('');
  const [isSending, setIsSending] = useState(false);

  const canSubmit = choiceA.trim().length > 0 && choiceB.trim().length > 0 && !isSending;

  async function handleSubmit() {
    if (!canSubmit) return;
    setIsSending(true);
    hapticImpact('light');

    try {
      const result = await api.addCard(choiceA.trim(), choiceB.trim(), currentUser.id);
      handleApiResponse(result);

      if (!result.error) {
        hapticNotification('success');
        showToast('Карточка отправлена на модерацию!');
        setTimeout(() => {
          closeMenu();
        }, 1800);
      } else {
        hapticNotification('error');
        showToast(typeof result.result === 'string' ? result.result : 'Ошибка модерации или отправки');
        setIsSending(false);
      }
    } catch (err) {
      console.error('Add card error:', err);
      hapticNotification('error');
      showToast('Ошибка отправки');
      setIsSending(false);
    }
  }

  const handleBack = () => {
    hapticImpact('light');
    onBack();
  };

  return (
    <div className="create-card custom-scroll">
      <button className="create-back" onClick={handleBack} aria-label="Назад">
        ← Назад
      </button>

      <h2 className="create-title">Создать карточку</h2>

      <div className="create-rules-box">
        <p className="create-rules">
          💡 <strong>Правила публикации:</strong> Запрещены нецензурные выражения, оскорбления и спам-ссылки. Все карточки проверяются перед публикацией.
        </p>
      </div>

      <div className="create-fields">
        <div className="create-field create-field--a">
          <textarea
            className="create-textarea"
            placeholder="Вариант А"
            value={choiceA}
            onChange={(e) => setChoiceA(e.target.value.slice(0, MAX_LENGTH))}
            maxLength={MAX_LENGTH}
            rows={3}
            disabled={isSending}
          />
          <span className="create-counter">
            {choiceA.length}/{MAX_LENGTH}
          </span>
        </div>

        <div className="create-field create-field--b">
          <textarea
            className="create-textarea"
            placeholder="Вариант Б"
            value={choiceB}
            onChange={(e) => setChoiceB(e.target.value.slice(0, MAX_LENGTH))}
            maxLength={MAX_LENGTH}
            rows={3}
            disabled={isSending}
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
        {isSending ? 'Отправка на модерацию...' : 'Отправить на модерацию'}
      </button>
    </div>
  );
}
