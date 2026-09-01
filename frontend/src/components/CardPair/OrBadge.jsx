import React from 'react';
import './OrBadge.css';

export default function OrBadge({ visible }) {
  return (
    <div className={`or-badge ${visible ? '' : 'or-badge--hidden'}`}>
      <span className="or-badge-text">ИЛИ</span>
    </div>
  );
}
