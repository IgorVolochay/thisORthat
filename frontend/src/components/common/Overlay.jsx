import React from 'react';
import './Overlay.css';

export default function Overlay({ visible, onClick }) {
  return (
    <div
      className={`overlay ${visible ? 'overlay--visible' : ''}`}
      onClick={onClick}
      aria-hidden="true"
    />
  );
}
