import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import LoadingScreen from './components/common/LoadingScreen';
import BannedScreen from './components/common/BannedScreen';
import Toast from './components/common/Toast';
import CardPair from './components/CardPair/CardPair';
import BottomBar from './components/BottomBar/BottomBar';
import CommentsPanel from './components/Comments/CommentsPanel';
import MenuPanel from './components/Menu/MenuPanel';
import './App.css';

function AppContent() {
  const { isLoading, error, isBanned, handleRetryAfterBan, openMenu, toast } = useApp();

  if (isBanned) {
    return <BannedScreen onRetry={handleRetryAfterBan} />;
  }

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (error && !isLoading) {
    return <LoadingScreen error={error} />;
  }

  return (
    <div className="app">
      {/* Header with menu button */}
      <header className="app-header">
        <div className="app-logo">
          this<span className="app-logo-or">OR</span>that
        </div>
        <button className="menu-toggle" onClick={openMenu} aria-label="Меню">
          <span className="menu-toggle-line" />
          <span className="menu-toggle-line" />
          <span className="menu-toggle-line" />
        </button>
      </header>

      {/* Main content — card pair */}
      <CardPair />

      {/* Bottom bar — reactions */}
      <BottomBar />

      {/* Panels */}
      <CommentsPanel />
      <MenuPanel />

      {/* Toast notifications */}
      <Toast message={toast} />
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
