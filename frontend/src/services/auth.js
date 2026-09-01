/**
 * Auth service — detects Telegram WebApp user or falls back to mock.
 * Provides Telegram Mini App initialization, initData extraction, and Haptic Feedback.
 */

const MOCK_USER = {
  id: 999995,
  first_name: 'Dev',
  last_name: 'User',
  username: 'devuser',
  photo_url: '',
};

/**
 * Extracts raw Telegram initData query-string for backend HMAC validation.
 */
export function getTelegramInitData() {
  try {
    return window.Telegram?.WebApp?.initData || '';
  } catch {
    return '';
  }
}

/**
 * Extracts parsed user info from initDataUnsafe for UI display.
 */
export function getTelegramUser() {
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

/**
 * Initializes Telegram WebApp environment (theme, fullscreen expand, close confirmation).
 */
export function initTelegramApp() {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor?.('#070711');
      tg.setBackgroundColor?.('#070711');
      tg.enableClosingConfirmation?.();
    } catch {
      // Ignored in unsupported client versions
    }
  }
}

/**
 * Triggers Telegram Haptic Feedback impact.
 * @param {'light' | 'medium' | 'heavy' | 'rigid' | 'soft'} style
 */
export function hapticImpact(style = 'light') {
  try {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred(style);
  } catch {}
}

/**
 * Triggers Telegram Haptic Feedback notification.
 * @param {'error' | 'success' | 'warning'} type
 */
export function hapticNotification(type = 'success') {
  try {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred(type);
  } catch {}
}

/**
 * Handles Telegram BackButton lifecycle with cleanup.
 */
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
  return () => {};
}

/**
 * Safely opens external link in Telegram WebApp or browser.
 */
export function openExternalLink(url) {
  try {
    if (window.Telegram?.WebApp?.openLink) {
      window.Telegram.WebApp.openLink(url);
      return;
    }
  } catch {}
  window.open(url, '_blank', 'noopener,noreferrer');
}
