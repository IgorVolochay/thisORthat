import React from 'react';
import './Card.css';

export default function Card({ label, type, chosen, isChosen, percent, count, onClick }) {
  const isRevealed = chosen !== null;
  const isThis = chosen === type;
  const isFaded = isRevealed && !isThis;

  const cardClass = [
    'card',
    `card--${type.toLowerCase()}`,
    isRevealed ? 'card--revealed' : '',
    isThis ? 'card--chosen' : '',
    isFaded ? 'card--faded' : '',
    isChosen ? 'card--tap-next' : '',
  ].filter(Boolean).join(' ');

  return (
    <button className={cardClass} onClick={onClick} aria-label={label}>
      <span className="card-text">{label}</span>
      {isRevealed && (
        <div className="card-stats">
          <span className="card-percent">{percent}%</span>
          <span className="card-count">{count}</span>
        </div>
      )}
      {isChosen && isRevealed && (
        <div className="card-hint">
          нажми чтобы продолжить
        </div>
      )}
    </button>
  );
}
