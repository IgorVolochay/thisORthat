import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { showBackButton } from '../../services/auth';
import { api } from '../../services/api';
import { currentUser } from '../../services/auth';
import CommentItem from './CommentItem';
import './CommentsPanel.css';

export default function CommentsPanel() {
  const { isCommentsOpen, setIsCommentsOpen, currentCard, showToast } = useApp();
  const [comments, setComments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [isSending, setIsSending] = useState(false);
  const listRef = useRef(null);

  // Telegram BackButton
  useEffect(() => {
    if (isCommentsOpen) {
      const cleanup = showBackButton(() => setIsCommentsOpen(false));
      return cleanup;
    }
  }, [isCommentsOpen, setIsCommentsOpen]);

  // Load comments when panel opens
  useEffect(() => {
    if (isCommentsOpen && currentCard) {
      loadComments();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCommentsOpen, currentCard?.card_id]);

  async function loadComments() {
    setIsLoading(true);
    try {
      // TODO: Replace with real GET /get_comments when backend implements it
      const result = await api.getComments(currentCard.card_id);
      if (!result.error) {
        setComments(result.result || []);
      }
    } catch (err) {
      console.error('Load comments error:', err);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSend() {
    if (!newComment.trim() || isSending) return;
    setIsSending(true);
    try {
      const result = await api.addComment(currentUser.id, currentCard.card_id, newComment.trim());
      if (!result.error) {
        setNewComment('');
        showToast('Комментарий отправлен');
        
        // Optimistically add the new comment to the list
        if (result.result) {
          setComments(prev => [...prev, result.result]);
          
          // Scroll to bottom after adding
          setTimeout(() => {
            if (listRef.current) {
              listRef.current.scrollTop = listRef.current.scrollHeight;
            }
          }, 100);
        }
      } else {
        showToast('Ошибка: ' + (result.result || 'неизвестная'));
      }
    } catch (err) {
      console.error('Send comment error:', err);
    } finally {
      setIsSending(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className={`comments-panel ${isCommentsOpen ? 'comments-panel--open' : ''}`}>
      <div className="comments-header">
        <button
          className="comments-close"
          onClick={() => setIsCommentsOpen(false)}
          aria-label="Закрыть"
        >
          ←
        </button>
        <h2 className="comments-title">Комментарии</h2>
      </div>

      <div className="comments-list custom-scroll" ref={listRef}>
        {isLoading ? (
          <p className="comments-placeholder">Загрузка...</p>
        ) : comments.length === 0 ? (
          <div className="comments-empty">
            <p className="comments-empty-text">Комментариев пока нет</p>
            <p className="comments-empty-sub">Будь первым!</p>
          </div>
        ) : (
          comments.map((comment, i) => (
            <CommentItem key={comment.comment_id || i} comment={comment} author={null} />
          ))
        )}
      </div>

      <div className="comments-input-area">
        <textarea
          className="comments-input"
          placeholder="Ваш комментарий..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={300}
          rows={1}
        />
        <button
          className={`comments-send ${newComment.trim() ? 'comments-send--active' : ''}`}
          onClick={handleSend}
          disabled={!newComment.trim() || isSending}
          aria-label="Отправить"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
