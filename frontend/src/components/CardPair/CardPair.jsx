import React from 'react';
import Card from './Card';
import OrBadge from './OrBadge';
import { useApp } from '../../context/AppContext';
import { openExternalLink, hapticImpact } from '../../services/auth';
import './CardPair.css';

export default function CardPair() {
  const { currentCard, chosenCard, chooseCard, loadCards, isLoadingCards, openMenu, setMenuScreen } = useApp();

  if (!currentCard) {
    return (
      <div className="card-pair card-pair--empty">
        <div className="empty-content">
          <div className="empty-badge-icon">✨</div>
          <h2 className="card-pair-empty-text">Карточки закончились!</h2>
          <p className="card-pair-empty-sub">
            Вы посмотрели все доступные карточки. Новые карточки появляются после прохождения модерации.
          </p>

          <div className="empty-actions">
            <button
              className="empty-btn empty-btn--refresh"
              onClick={() => loadCards(true)}
              disabled={isLoadingCards}
            >
              <svg
                className={`refresh-icon ${isLoadingCards ? 'refresh-icon--spinning' : ''}`}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                width="18"
                height="18"
              >
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 11-.57-8.38l5.67-5.67" />
              </svg>
              <span>{isLoadingCards ? 'Проверяем...' : 'Проверить новые карточки'}</span>
            </button>

            <button
              className="empty-btn empty-btn--primary"
              onClick={() => {
                openMenu();
                setMenuScreen('create');
              }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
                <path d="M12 5v14M5 12h14" />
              </svg>
              <span>Создать карточку</span>
            </button>

            <button
              className="empty-btn"
              onClick={() => {
                openMenu();
                setMenuScreen('about');
              }}
            >
              О проекте
            </button>

            <button
              className="empty-btn empty-btn--donate"
              onClick={() => {
                hapticImpact('light');
                openExternalLink('https://boosty.to/pseudodev/donate');
              }}
            >
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
    // Add current user's choice for visual distribution
    const votesA = currentCard.count_choice_A + (chosenCard === 'A' ? 1 : 0);
    const votesB = currentCard.count_choice_B + (chosenCard === 'B' ? 1 : 0);
    const newTotal = votesA + votesB;
    if (newTotal > 0) {
      percentA = Math.round((votesA / newTotal) * 100);
      percentB = 100 - percentA;
    }

    // Clamp between 25% and 75% for readable card size balance
    if (percentA > 75) {
      percentA = 75;
      percentB = 25;
    }
    if (percentB > 75) {
      percentB = 75;
      percentA = 25;
    }
  }

  // flex-grow values for smooth spring animation
  const growA = chosenCard ? percentA : 50;
  const growB = chosenCard ? percentB : 50;

  // Actual display percentages
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
