import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { showBackButton, currentUser, hapticNotification, hapticImpact } from '../../services/auth';
import { api } from '../../services/api';
import CommentItem from './CommentItem';
import './CommentsPanel.css';

export default function CommentsPanel() {
  const {
    isCommentsOpen,
    setIsCommentsOpen,
    currentCard,
    showToast,
    getUserProfile,
    handleApiResponse,
    syncCardComments,
    addCommentToCard,
  } = useApp();
  const [comments, setComments] = useState([]);
  const [authors, setAuthors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [isSending, setIsSending] = useState(false);
  const listRef = useRef(null);

  // Telegram BackButton
  useEffect(() => {
    if (isCommentsOpen) {
      const cleanup = showBackButton(() => {
        hapticImpact('light');
        setIsCommentsOpen(false);
      });
      return cleanup;
    }
  }, [isCommentsOpen, setIsCommentsOpen]);

  const cardId = currentCard?.card_id;

  const loadComments = useCallback(async () => {
    if (!cardId) return;
    setIsLoading(true);

    try {
      const result = await api.getComments(cardId);
      handleApiResponse(result);

      if (!result.error && Array.isArray(result.result)) {
        const loadedComments = result.result;
        setComments(loadedComments);
        syncCardComments(cardId, loadedComments.map((c) => c.comment_id));

        // Fetch author profiles for all unique authors
        const uniqueAuthorIds = Array.from(new Set(loadedComments.map((c) => c.author_id)));
        const authorsData = {};

        await Promise.all(
          uniqueAuthorIds.map(async (authorId) => {
            const profile = await getUserProfile(authorId);
            if (profile) {
              authorsData[authorId] = profile;
            }
          })
        );

        setAuthors(authorsData);
      } else {
        setComments([]);
      }
    } catch (err) {
      console.error('Load comments error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [cardId, getUserProfile, handleApiResponse, syncCardComments]);

  // Load comments only when panel opens or active card ID changes
  useEffect(() => {
    if (isCommentsOpen && cardId) {
      loadComments();
    }
  }, [isCommentsOpen, cardId, loadComments]);

  async function handleSend() {
    const text = newComment.trim();
    if (!text || isSending || !currentCard) return;

    setIsSending(true);
    hapticImpact('light');

    try {
      const result = await api.addComment(currentUser.id, currentCard.card_id, text);
      handleApiResponse(result);

      if (!result.error && result.result) {
        setNewComment('');
        showToast('Комментарий опубликован');
        hapticNotification('success');

        const createdComment = result.result;
        setComments((prev) => [...prev, createdComment]);
        addCommentToCard(currentCard.card_id, createdComment.comment_id);

        // Add current user to authors map
        setAuthors((prev) => ({
          ...prev,
          [currentUser.id]: currentUser,
        }));

        // Scroll to bottom
        setTimeout(() => {
          if (listRef.current) {
            listRef.current.scrollTop = listRef.current.scrollHeight;
          }
        }, 100);
      } else {
        showToast(typeof result.result === 'string' ? result.result : 'Ошибка отправки комментария');
        hapticNotification('error');
      }
    } catch (err) {
      console.error('Send comment error:', err);
      showToast('Ошибка отправки');
      hapticNotification('error');
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

  const handleClose = () => {
    hapticImpact('light');
    setIsCommentsOpen(false);
  };

  return (
    <div className={`comments-panel ${isCommentsOpen ? 'comments-panel--open' : ''}`}>
      <div className="comments-header">
        <button
          className="comments-close"
          onClick={handleClose}
          aria-label="Закрыть"
        >
          ←
        </button>
        <h2 className="comments-title">Комментарии</h2>
        <span className="comments-count">{comments.length}</span>
      </div>

      <div className="comments-list custom-scroll" ref={listRef}>
        {isLoading ? (
          <div className="comments-loading">
            <div className="comments-spinner" />
            <p className="comments-placeholder">Загрузка комментариев...</p>
          </div>
        ) : comments.length === 0 ? (
          <div className="comments-empty">
            <div className="comments-empty-icon">💬</div>
            <p className="comments-empty-text">Комментариев пока нет</p>
            <p className="comments-empty-sub">Будь первым, кто поделится мнением!</p>
          </div>
        ) : (
          comments.map((comment, i) => (
            <CommentItem
              key={comment.comment_id || i}
              comment={comment}
              author={authors[comment.author_id] || null}
            />
          ))
        )}
      </div>

      <div className="comments-input-area">
        <textarea
          className="comments-input"
          placeholder="Напишите комментарий..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={300}
          rows={1}
          disabled={isSending}
        />
        <button
          className={`comments-send ${newComment.trim() && !isSending ? 'comments-send--active' : ''}`}
          onClick={handleSend}
          disabled={!newComment.trim() || isSending}
          aria-label="Отправить"
        >
          {isSending ? (
            <span className="comments-btn-spinner" />
          ) : (
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
