import React from 'react';
import Card from './Card';
import OrBadge from './OrBadge';
import { useApp } from '../../context/AppContext';
import './CardPair.css';

export default function CardPair() {
  const { currentCard, chosenCard, chooseCard, openMenu, setMenuScreen } = useApp();

  if (!currentCard) {
    return (
      <div className="card-pair card-pair--empty">
        <div className="empty-content">
          <p className="card-pair-empty-text">Карточки закончились!</p>
          <div className="empty-actions">
            <button className="empty-btn empty-btn--primary" onClick={() => { openMenu(); setMenuScreen('create'); }}>
              Создать карточку
            </button>
            <button className="empty-btn" onClick={() => { openMenu(); setMenuScreen('about'); }}>
              О проекте
            </button>
            <button className="empty-btn" onClick={() => window.open('https://boosty.to/pseudodev/donate', '_blank')}>
              Поддержать проект
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Calculate percentages
  const total = currentCard.count_choice_A + currentCard.count_choice_B;
  let percentA = 50;
  let percentB = 50;

  if (chosenCard) {
    // Add the current user's vote to the count for display
    const votesA = currentCard.count_choice_A + (chosenCard === 'A' ? 1 : 0);
    const votesB = currentCard.count_choice_B + (chosenCard === 'B' ? 1 : 0);
    const newTotal = votesA + votesB;
    if (newTotal > 0) {
      percentA = Math.round((votesA / newTotal) * 100);
      percentB = 100 - percentA;
    }

    // Clamp to 75/25 max for readability
    if (percentA > 75) { percentA = 75; percentB = 25; }
    if (percentB > 75) { percentB = 75; percentA = 25; }
  }

  // flex-grow values for animation
  const growA = chosenCard ? percentA : 50;
  const growB = chosenCard ? percentB : 50;

  // Actual percentages for display (unclamped)
  let displayPercentA = 50;
  let displayPercentB = 50;
  if (chosenCard && total >= 0) {
    const votesA = currentCard.count_choice_A + (chosenCard === 'A' ? 1 : 0);
    const votesB = currentCard.count_choice_B + (chosenCard === 'B' ? 1 : 0);
    const newTotal = votesA + votesB;
    if (newTotal > 0) {
      displayPercentA = Math.round((votesA / newTotal) * 100);
      displayPercentB = 100 - displayPercentA;
    }
  }

  return (
    <div className="card-pair">
      <div className="card-pair-inner">
        <div className="card-wrapper" style={{ flexGrow: growA }}>
          <Card
            label={currentCard.choice_A}
            type="A"
            chosen={chosenCard}
            isChosen={chosenCard === 'A'}
            percent={displayPercentA}
            count={currentCard.count_choice_A + (chosenCard === 'A' ? 1 : 0)}
            onClick={() => chooseCard('A')}
          />
        </div>

        <OrBadge visible={!chosenCard} />

        <div className="card-wrapper" style={{ flexGrow: growB }}>
          <Card
            label={currentCard.choice_B}
            type="B"
            chosen={chosenCard}
            isChosen={chosenCard === 'B'}
            percent={displayPercentB}
            count={currentCard.count_choice_B + (chosenCard === 'B' ? 1 : 0)}
            onClick={() => chooseCard('B')}
          />
        </div>
      </div>
    </div>
  );
}
