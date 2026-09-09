import React from 'react';
import './LoadingScreen.css';

export default function LoadingScreen({ error }) {
  return (
    <div className="loading-screen">
      <div className="loading-content">
        <h1 className="loading-title">
          this<span className="loading-or">OR</span>that
        </h1>
        {error ? (
          <p className="loading-error">{error}</p>
        ) : (
          <div className="loading-dots">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </div>
        )}
      </div>
    </div>
  );
}
