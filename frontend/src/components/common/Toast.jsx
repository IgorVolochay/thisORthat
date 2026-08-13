import React from 'react';
import './Toast.css';

export default function Toast({ message }) {
  if (!message) return null;

  return (
    <div className="toast" role="status" aria-live="polite">
      <div className="toast-content">
        <span className="toast-icon">✓</span>
        <span className="toast-text">{message}</span>
      </div>
    </div>
  );
}
