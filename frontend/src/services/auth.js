/**
 * Auth service — detects Telegram WebApp user or falls back to mock.
 * Auto-registers user on backend if not yet registered.
 */

const MOCK_USER = {
  id: 999995,
  first_name: 'Dev',
  last_name: 'User',
  username: 'devuser',
  photo_url: '',
};

function getTelegramUser() {
  try {
    const tg = window.Telegram?.WebApp;
    const user = tg?.initDataUnsafe?.user;
    if (user && user.id) {
      return {
        id: user.id,
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        username: user.username || '',
        photo_url: user.photo_url || '',
      };
    }
  } catch {
    // Telegram SDK not available
  }
  return null;
}

export const currentUser = getTelegramUser() ?? MOCK_USER;
export const isTelegram = !!getTelegramUser();

export function initTelegramApp() {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
  }
}

export function showBackButton(onBack) {
  const tg = window.Telegram?.WebApp;
  if (tg?.BackButton) {
    tg.BackButton.show();
    tg.BackButton.onClick(onBack);
    return () => {
      tg.BackButton.offClick(onBack);
      tg.BackButton.hide();
    };
  }
  return () => { };
}
