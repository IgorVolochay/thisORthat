import React from 'react';
import './AboutPage.css';

export default function AboutPage({ onBack }) {
  function handleCopyEmail() {
    navigator.clipboard.writeText('pseudo.developer.ru@gmail.com').then(() => {
      // Visual feedback handled by CSS :active
    }).catch(() => {
      // Fallback — select text
    });
  }

  return (
    <div className="about-page custom-scroll">
      <button className="about-back" onClick={onBack} aria-label="Назад">
        ← Назад
      </button>

      <h2 className="about-title">О проекте</h2>

      <div className="about-content">
        <p>
          <strong>This OR That</strong> — это open-source Telegram Mini App, 
          в которой ты выбираешь один из двух вариантов и смотришь, 
          что выбрали другие.
        </p>
        <p>
          Проект создан для развлечения и исследования интересных 
          дилемм. Все карточки проходят модерацию перед публикацией.
        </p>
        <p>
          Поддержи проект или загляни в исходный код — 
          мы открыты для идей и контрибьюций!
        </p>
      </div>

      <div className="about-links">
        <a
          href="https://github.com/IgorVolochay/thisORthat"
          target="_blank"
          rel="noopener noreferrer"
          className="about-link"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
          <span>Исходники проекта</span>
        </a>

        <button className="about-link" onClick={handleCopyEmail}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="20" height="20">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
            <polyline points="22,6 12,13 2,6" />
          </svg>
          <span>pseudo.developer.ru@gmail.com</span>
        </button>
      </div>
    </div>
  );
}
