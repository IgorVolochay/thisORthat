import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { currentUser, initTelegramApp, hapticImpact, hapticNotification } from '../services/auth';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  // App state
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);
  const [isBanned, setIsBanned] = useState(false);

  // Card queue
  const [cardQueue, setCardQueue] = useState([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [chosenCard, setChosenCard] = useState(null); // null | "A" | "B"
  const [isLoadingCards, setIsLoadingCards] = useState(false);

  // Panels
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isCommentsOpen, setIsCommentsOpen] = useState(false);
  const [menuScreen, setMenuScreen] = useState('menu'); // 'menu' | 'about' | 'create'

  // Toast
  const [toast, setToast] = useState(null);
  const toastTimeoutRef = useRef(null);

  // User Profile Cache for comments
  const userProfileCacheRef = useRef(new Map());

  // Initialization ref for React StrictMode
  const isInitializingRef = useRef(false);

  // Current card helper
  const currentCard = cardQueue[currentCardIndex] || null;

  // Toast helper
  const showToast = useCallback((message, duration = 2500) => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }
    setToast(message);
    toastTimeoutRef.current = setTimeout(() => setToast(null), duration);
  }, []);

  // Response interceptor helper
  const handleApiResponse = useCallback((res) => {
    if (res?.isBanned) {
      setIsBanned(true);
    }
    if (res?.status === 429) {
      showToast(typeof res.result === 'string' ? res.result : 'Слишком много запросов. Подождите немного.');
    }
    return res;
  }, [showToast]);

  // Load cards batch
  const loadCards = useCallback(async (isManualRefresh = false) => {
    setIsLoadingCards(true);
    if (isManualRefresh) {
      hapticImpact('light');
    }

    try {
      const result = await api.getRandomCards(currentUser.id);
      handleApiResponse(result);

      if (!result.error && Array.isArray(result.result) && result.result.length > 0) {
        setCardQueue(result.result);
        setCurrentCardIndex(0);
        setChosenCard(null);
        if (isManualRefresh) {
          showToast('Карточки обновлены!');
          hapticNotification('success');
        }
      } else {
        // Pool is empty or all cards seen
        setCardQueue([]);
        setCurrentCardIndex(0);
        setChosenCard(null);
        if (isManualRefresh) {
          showToast('Новых карточек пока нет');
        }
      }
    } catch (err) {
      console.error('Load cards error:', err);
      if (isManualRefresh) {
        showToast('Ошибка загрузки карточек');
      }
    } finally {
      setIsLoadingCards(false);
    }
  }, [handleApiResponse, showToast]);

  // Initialize app
  const initApp = useCallback(async () => {
    try {
      initTelegramApp();

      // Check/register user
      const checkResult = await api.checkUser(currentUser.id);
      handleApiResponse(checkResult);
      if (checkResult?.isBanned) return;

      if (!checkResult.error && !checkResult.result) {
        const addResult = await api.addUser({
          user_id: currentUser.id,
          username: currentUser.username,
          first_name: currentUser.first_name,
          last_name: currentUser.last_name,
          photo_url: currentUser.photo_url,
        });
        handleApiResponse(addResult);
        if (addResult?.isBanned) return;
      }

      const userResult = await api.getUser(currentUser.id);
      handleApiResponse(userResult);
      if (userResult?.isBanned) return;

      if (!userResult.error && userResult.result) {
        setUser(userResult.result);
      }

      // Load first batch of cards
      await loadCards();
    } catch (err) {
      setError('Не удалось загрузить приложение');
      console.error('Init error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [handleApiResponse, loadCards]);

  useEffect(() => {
    if (isInitializingRef.current) return;
    isInitializingRef.current = true;
    initApp();
  }, [initApp]);

  // User Profile resolver for comments
  const getUserProfile = useCallback(async (userId) => {
    if (!userId) return null;
    if (userId === currentUser.id) {
      return {
        user_id: currentUser.id,
        username: currentUser.username,
        first_name: currentUser.first_name,
        last_name: currentUser.last_name,
        photo_url: currentUser.photo_url,
      };
    }
    if (userProfileCacheRef.current.has(userId)) {
      return userProfileCacheRef.current.get(userId);
    }
    try {
      const res = await api.getUser(userId);
      handleApiResponse(res);
      if (!res.error && res.result) {
        userProfileCacheRef.current.set(userId, res.result);
        return res.result;
      }
    } catch (err) {
      console.error('Failed to get user profile:', userId, err);
    }
    return null;
  }, [handleApiResponse]);

  // Go to next card
  const goToNextCard = useCallback(async () => {
    hapticImpact('light');
    const nextIndex = currentCardIndex + 1;
    if (nextIndex < cardQueue.length) {
      setCurrentCardIndex(nextIndex);
      setChosenCard(null);
    } else {
      // Load next batch
      await loadCards();
    }
  }, [currentCardIndex, cardQueue.length, loadCards]);

  // Choose a card (A or B)
  const chooseCard = useCallback((choice) => {
    if (chosenCard) {
      // Second tap on chosen card — go next
      if (choice === chosenCard) {
        goToNextCard();
      }
      return;
    }

    hapticImpact('medium');
    setChosenCard(choice);

    if (currentCard) {
      api.selectChoice(currentUser.id, currentCard.card_id, choice)
        .then(handleApiResponse)
        .catch(console.error);
    }
  }, [chosenCard, currentCard, goToNextCard, handleApiResponse]);

  const syncCardComments = useCallback((cardId, commentsArrayOrIds) => {
    if (!Array.isArray(commentsArrayOrIds)) return;
    setCardQueue((prev) => {
      const targetCard = prev.find((c) => c.card_id === cardId);
      if (!targetCard) return prev;
      if (targetCard.comments && targetCard.comments.length === commentsArrayOrIds.length) {
        return prev; // No change, avoid re-render
      }
      return prev.map((c) =>
        c.card_id === cardId
          ? { ...c, comments: commentsArrayOrIds }
          : c
      );
    });
  }, []);

  const addCommentToCard = useCallback((cardId, commentId) => {
    setCardQueue((prev) =>
      prev.map((c) =>
        c.card_id === cardId
          ? {
            ...c,
            comments: c.comments ? [...c.comments, commentId] : [commentId],
          }
          : c
      )
    );
  }, []);

  // Auto-sync real comments count for current card from /get_comments
  useEffect(() => {
    const cardId = currentCard?.card_id;
    if (!cardId) return;

    let isMounted = true;
    api.getComments(cardId)
      .then((res) => {
        if (isMounted && !res.error && Array.isArray(res.result)) {
          syncCardComments(cardId, res.result.map((c) => c.comment_id));
        }
      })
      .catch(() => { });

    return () => {
      isMounted = false;
    };
  }, [currentCard?.card_id, syncCardComments]);

  // Reactions
  const likeCard = useCallback(async () => {
    if (!currentCard || !chosenCard) return;
    hapticImpact('light');

    const result = await api.likeCard(currentUser.id, currentCard.card_id);
    handleApiResponse(result);

    if (result && !result.error) {
      // Update local card counts in cardQueue
      setCardQueue((prev) =>
        prev.map((c) =>
          c.card_id === currentCard.card_id
            ? { ...c, count_likes: (c.count_likes || 0) + 1 }
            : c
        )
      );

      // Refresh user data for liked_card_ids
      const userResult = await api.getUser(currentUser.id);
      handleApiResponse(userResult);
      if (!userResult.error && userResult.result) {
        setUser(userResult.result);
      }
    }
    return result;
  }, [currentCard, chosenCard, handleApiResponse]);

  const dislikeCard = useCallback(async () => {
    if (!currentCard || !chosenCard) return;
    hapticImpact('light');

    const result = await api.dislikeCard(currentUser.id, currentCard.card_id);
    handleApiResponse(result);

    if (result && !result.error) {
      // Update local card counts in cardQueue
      setCardQueue((prev) =>
        prev.map((c) =>
          c.card_id === currentCard.card_id
            ? { ...c, count_dislikes: (c.count_dislikes || 0) + 1 }
            : c
        )
      );

      // Refresh user data for disliked_card_ids
      const userResult = await api.getUser(currentUser.id);
      handleApiResponse(userResult);
      if (!userResult.error && userResult.result) {
        setUser(userResult.result);
      }
    }
    return result;
  }, [currentCard, chosenCard, handleApiResponse]);

  // Menu helpers
  const openMenu = useCallback(() => {
    hapticImpact('light');
    setIsMenuOpen(true);
    setMenuScreen('menu');
  }, []);

  const closeMenu = useCallback(() => {
    hapticImpact('light');
    setIsMenuOpen(false);
    setMenuScreen('menu');
  }, []);

  const handleRetryAfterBan = useCallback(() => {
    setIsBanned(false);
    setIsLoading(true);
    initApp();
  }, [initApp]);

  const value = {
    // State
    isLoading,
    isLoadingCards,
    user,
    error,
    isBanned,
    currentCard,
    chosenCard,
    cardQueue,
    currentCardIndex,
    isMenuOpen,
    isCommentsOpen,
    menuScreen,
    toast,

    // Actions
    chooseCard,
    goToNextCard,
    loadCards,
    likeCard,
    dislikeCard,
    getUserProfile,
    handleApiResponse,
    syncCardComments,
    addCommentToCard,
    openMenu,
    closeMenu,
    setMenuScreen,
    setIsCommentsOpen,
    showToast,
    setError,
    handleRetryAfterBan,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}
