import React, { useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { showBackButton, hapticImpact, openExternalLink } from '../../services/auth';
import Overlay from '../common/Overlay';
import AboutPage from './AboutPage';
import CreateCard from './CreateCard';
import './MenuPanel.css';

export default function MenuPanel() {
  const { isMenuOpen, closeMenu, menuScreen, setMenuScreen } = useApp();

  // Telegram BackButton for sub-screens
  useEffect(() => {
    if (isMenuOpen && menuScreen !== 'menu') {
      const cleanup = showBackButton(() => {
        hapticImpact('light');
        setMenuScreen('menu');
      });
      return cleanup;
    }
    if (isMenuOpen && menuScreen === 'menu') {
      const cleanup = showBackButton(() => {
        hapticImpact('light');
        closeMenu();
      });
      return cleanup;
    }
  }, [isMenuOpen, menuScreen, setMenuScreen, closeMenu]);

  if (!isMenuOpen) return null;

  const handleNavigate = (screen) => {
    hapticImpact('light');
    setMenuScreen(screen);
  };

  const handleExternalLink = (url) => {
    hapticImpact('light');
    openExternalLink(url);
  };

  // Sub-screens
  if (menuScreen === 'about') {
    return (
      <>
        <Overlay visible={true} onClick={closeMenu} />
        <div className="menu-panel menu-panel--open">
          <AboutPage onBack={() => handleNavigate('menu')} />
        </div>
      </>
    );
  }

  if (menuScreen === 'create') {
    return (
      <>
        <Overlay visible={true} onClick={closeMenu} />
        <div className="menu-panel menu-panel--open">
          <CreateCard onBack={() => handleNavigate('menu')} />
        </div>
      </>
    );
  }

  return (
    <>
      <Overlay visible={true} onClick={closeMenu} />
      <div className="menu-panel menu-panel--open">
        <nav className="menu-list">
          <button className="menu-item" onClick={() => handleNavigate('about')}>
            <span className="menu-icon">
              <svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22">
                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
                <path d="M12 16v-4M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </span>
            <span className="menu-label">О проекте</span>
          </button>

          <button className="menu-item" onClick={() => handleNavigate('create')}>
            <span className="menu-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="22" height="22">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </span>
            <span className="menu-label">Создать карточку</span>
          </button>

          <button
            className="menu-item"
            onClick={() => handleExternalLink('https://boosty.to/pseudodev/donate')}
          >
            <span className="menu-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="22" height="22">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
              </svg>
            </span>
            <span className="menu-label">Поддержать проект</span>
          </button>
        </nav>
      </div>
    </>
  );
}
