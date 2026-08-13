import React from 'react';
import './CommentItem.css';

export default function CommentItem({ comment, author }) {
  const displayName = author?.username || author?.first_name || 'Аноним';
  const date = comment.creation_date
    ? new Date(comment.creation_date).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      })
    : '';

  return (
    <div className="comment-item">
      <div className="comment-avatar">
        {author?.photo_url ? (
          <img src={author.photo_url} alt="" className="comment-avatar-img" />
        ) : (
          <span className="comment-avatar-fallback">
            {displayName[0]?.toUpperCase() || '?'}
          </span>
        )}
      </div>
      <div className="comment-body">
        <div className="comment-header">
          <span className="comment-author">{displayName}</span>
          <span className="comment-date">{date}</span>
        </div>
        <p className="comment-text">{comment.comment_text || comment.commet_text}</p>
      </div>
    </div>
  );
}
