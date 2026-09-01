import React, { useState, useEffect } from 'react';
import { currentUser } from '../../services/auth';
import './CommentItem.css';

export default function CommentItem({ comment, author }) {
  const [imageError, setImageError] = useState(false);
  const isMe = comment.author_id === currentUser?.id;
  
  const displayName = isMe 
    ? (currentUser?.username ? `@${currentUser.username}` : currentUser?.first_name || 'Вы')
    : (author?.username ? `@${author.username}` : author?.first_name || `Игрок #${comment.author_id}`);

  const photoUrl = isMe ? currentUser?.photo_url : author?.photo_url;

  useEffect(() => {
    setImageError(false);
  }, [photoUrl]);

  const dateStr = comment.creation_date
    ? new Date(comment.creation_date).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  const initial = displayName.replace(/^@/, '')[0]?.toUpperCase() || '?';

  return (
    <div className={`comment-item ${isMe ? 'comment-item--me' : ''}`}>
      <div className="comment-avatar">
        {photoUrl && !imageError ? (
          <img
            src={photoUrl}
            alt=""
            className="comment-avatar-img"
            referrerPolicy="no-referrer"
            onError={() => setImageError(true)}
          />
        ) : (
          <span className={`comment-avatar-fallback ${isMe ? 'comment-avatar-fallback--me' : ''}`}>
            {initial}
          </span>
        )}
      </div>

      <div className="comment-body">
        <div className="comment-header">
          <div className="comment-author-group">
            <span className="comment-author">{displayName}</span>
            {isMe && <span className="comment-me-badge">Вы</span>}
          </div>
          <span className="comment-date">{dateStr}</span>
        </div>
        <p className="comment-text">{comment.comment_text || comment.commet_text}</p>
      </div>
    </div>
  );
}
