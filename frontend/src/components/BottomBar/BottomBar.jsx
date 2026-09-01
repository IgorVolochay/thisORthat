import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import './BottomBar.css';

export default function BottomBar() {
  const { currentCard, chosenCard, likeCard, dislikeCard, setIsCommentsOpen, user } = useApp();
  const [reactionState, setReactionState] = useState(null); // 'liked' | 'disliked' | null

  const isRevealed = chosenCard !== null;

  // Check if user already reacted to this card
  const alreadyLiked = user?.liked_card_ids?.includes(currentCard?.card_id);
  const alreadyDisliked = user?.disliked_card_ids?.includes(currentCard?.card_id);
  const currentReaction = reactionState || (alreadyLiked ? 'liked' : alreadyDisliked ? 'disliked' : null);

  const handleLike = async () => {
    if (!isRevealed || currentReaction) return;
    const result = await likeCard();
    if (result && !result.error) {
      setReactionState('liked');
    }
  };

  const handleDislike = async () => {
    if (!isRevealed || currentReaction) return;
    const result = await dislikeCard();
    if (result && !result.error) {
      setReactionState('disliked');
    }
  };

  const handleComments = () => {
    setIsCommentsOpen(true);
  };

  // Reset reaction state when card changes
  React.useEffect(() => {
    setReactionState(null);
  }, [currentCard?.card_id]);

  const likes = (currentCard?.count_likes || 0) + (reactionState === 'liked' ? 1 : 0);
  const dislikes = (currentCard?.count_dislikes || 0) + (reactionState === 'disliked' ? 1 : 0);

  return (
    <div className="bottom-bar">
      <button
        className={`bar-btn bar-btn--dislike ${currentReaction === 'disliked' ? 'bar-btn--active' : ''} ${!isRevealed || currentReaction ? 'bar-btn--disabled' : ''}`}
        onClick={handleDislike}
        aria-label="Дизлайк"
      >
        <svg className="bar-icon" viewBox="0 0 24 24" fill="currentColor" style={{ transform: 'rotate(180deg)' }}>
          <path d="M17 4h2a2 2 0 012 2v7a2 2 0 01-2 2h-2.29a1 1 0 00-.71.3l-3.28 3.28a1 1 0 01-1.72-.7V15a1 1 0 00-1-1H7a2 2 0 01-2-2V6a2 2 0 012-2h10z" />
        </svg>
        <span className="bar-count">{formatCount(dislikes)}</span>
      </button>

      <button
        className="bar-btn bar-btn--comments"
        onClick={handleComments}
        aria-label="Комментарии"
      >
        <svg className="bar-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z" />
        </svg>
        <span className="bar-count">{formatCount(currentCard?.comments?.length || 0)}</span>
      </button>

      <button
        className={`bar-btn bar-btn--like ${currentReaction === 'liked' ? 'bar-btn--active' : ''} ${!isRevealed || currentReaction ? 'bar-btn--disabled' : ''}`}
        onClick={handleLike}
        aria-label="Лайк"
      >
        <svg className="bar-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17 4h2a2 2 0 012 2v7a2 2 0 01-2 2h-2.29a1 1 0 00-.71.3l-3.28 3.28a1 1 0 01-1.72-.7V15a1 1 0 00-1-1H7a2 2 0 01-2-2V6a2 2 0 012-2h10z" />
        </svg>
        <span className="bar-count">{formatCount(likes)}</span>
      </button>
    </div>
  );
}

function formatCount(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, '') + 'K';
  return String(n);
}
