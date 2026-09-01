import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';
import { currentUser, initTelegramApp } from '../services/auth';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  // App state
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);

  // Card queue
  const [cardQueue, setCardQueue] = useState([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [chosenCard, setChosenCard] = useState(null); // null | "A" | "B"

  // Panels
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isCommentsOpen, setIsCommentsOpen] = useState(false);
  const [menuScreen, setMenuScreen] = useState('menu'); // 'menu' | 'about' | 'create'

  // Toast
  const [toast, setToast] = useState(null);

  // Current card helper
  const currentCard = cardQueue[currentCardIndex] || null;

  // Initialize app
  useEffect(() => {
    async function init() {
      try {
        initTelegramApp();

        // Check/register user
        const checkResult = await api.checkUser(currentUser.id);
        if (!checkResult.result) {
          await api.addUser({
            user_id: currentUser.id,
            username: currentUser.username,
            first_name: currentUser.first_name,
            last_name: currentUser.last_name,
            photo_url: currentUser.photo_url,
          });
        }

        const userResult = await api.getUser(currentUser.id);
        if (!userResult.error) {
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
    }
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load cards batch
  const loadCards = useCallback(async () => {
    try {
      const result = await api.getRandomCards(currentUser.id);
      if (!result.error && Array.isArray(result.result) && result.result.length > 0) {
        setCardQueue(result.result);
        setCurrentCardIndex(0);
        setChosenCard(null);
      } else {
        // No more cards or error
        setCardQueue([]);
        setCurrentCardIndex(0);
      }
    } catch (err) {
      console.error('Load cards error:', err);
      setError('Ошибка загрузки карточек');
    }
  }, []);

  // Choose a card (A or B)
  const chooseCard = useCallback((choice) => {
    if (chosenCard) {
      // Second tap on chosen card — go next
      if (choice === chosenCard) {
        goToNextCard();
      }
      return;
    }
    setChosenCard(choice);
    // Fire select_choice to backend
    if (currentCard) {
      api.selectChoice(currentUser.id, currentCard.card_id, choice).catch(console.error);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chosenCard, currentCard]);

  // Go to next card
  const goToNextCard = useCallback(async () => {
    const nextIndex = currentCardIndex + 1;
    if (nextIndex < cardQueue.length) {
      setCurrentCardIndex(nextIndex);
      setChosenCard(null);
    } else {
      // Load next batch
      await loadCards();
    }
  }, [currentCardIndex, cardQueue.length, loadCards]);

  // Reactions
  const likeCard = useCallback(async () => {
    if (!currentCard || !chosenCard) return;
    const result = await api.likeCard(currentUser.id, currentCard.card_id);
    if (!result.error) {
      // Refresh user data to get updated liked_card_ids
      const userResult = await api.getUser(currentUser.id);
      if (!userResult.error) setUser(userResult.result);
    }
    return result;
  }, [currentCard, chosenCard]);

  const dislikeCard = useCallback(async () => {
    if (!currentCard || !chosenCard) return;
    const result = await api.dislikeCard(currentUser.id, currentCard.card_id);
    if (!result.error) {
      const userResult = await api.getUser(currentUser.id);
      if (!userResult.error) setUser(userResult.result);
    }
    return result;
  }, [currentCard, chosenCard]);

  // Toast helper
  const showToast = useCallback((message, duration = 2500) => {
    setToast(message);
    setTimeout(() => setToast(null), duration);
  }, []);

  // Menu helpers
  const openMenu = useCallback(() => {
    setIsMenuOpen(true);
    setMenuScreen('menu');
  }, []);

  const closeMenu = useCallback(() => {
    setIsMenuOpen(false);
    setMenuScreen('menu');
  }, []);

  const value = {
    // State
    isLoading,
    user,
    error,
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
    openMenu,
    closeMenu,
    setMenuScreen,
    setIsCommentsOpen,
    showToast,
    setError,
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
