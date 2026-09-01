import React from 'react';
import './BannedScreen.css';

export default function BannedScreen({ onRetry }) {
  const handleSupportClick = () => {
    window.open('https://t.me/IgorVolochay', '_blank');
  };

  return (
    <div className="banned-screen">
      <div className="banned-card">
        <div className="banned-icon-wrapper">
          <svg className="banned-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        <h1 className="banned-title">Доступ ограничен</h1>

        <p className="banned-subtitle">
          Система безопасности зафиксировала подозрительную активность с вашего IP-адреса.
        </p>

        <div className="banned-info-box">
          <div className="banned-info-dot" />
          <span>Блокировка длится 1 час и снимается автоматически.</span>
        </div>

        <div className="banned-actions">
          {onRetry && (
            <button className="banned-btn banned-btn--primary" onClick={onRetry}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 11-.57-8.38l5.67-5.67" />
              </svg>
              <span>Повторить попытку</span>
            </button>
          )}

          <button className="banned-btn banned-btn--secondary" onClick={handleSupportClick}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
              <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
            </svg>
            <span>Написать в поддержку</span>
          </button>
        </div>
      </div>
    </div>
  );
}
