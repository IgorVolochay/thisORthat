/**
 * API service — all backend requests for This OR That.
 * Includes X-Init-Data header injection, rate limit handling, and IP ban detection.
 * All endpoints return { result, error, status, isBanned }.
 */

import { getTelegramInitData } from './auth';

const BASE_URL = process.env.REACT_APP_API_URL || '';

async function request(method, path, body = null) {
  const headers = {
    'Content-Type': 'application/json',
  };

  const initData = getTelegramInitData();
  if (initData) {
    headers['X-Init-Data'] = initData;
  }

  const options = {
    method,
    headers,
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${BASE_URL}${path}`, options);
    let data;
    try {
      data = await response.json();
    } catch {
      data = { result: response.statusText, error: !response.ok };
    }

    // Check for IP ban by FastAPI-guard / penetration detection
    const isIpBanned = response.status === 403 && (
      (typeof data?.detail === 'string' && /banned|ip.*banned|suspicious/i.test(data.detail)) ||
      (typeof data?.result === 'string' && /banned|ip.*banned|suspicious/i.test(data.result))
    );

    if (!response.ok) {
      if (response.status === 429) {
        return {
          result: data?.detail || 'Слишком много запросов. Подождите несколько секунд.',
          error: true,
          status: 429,
          isBanned: false,
        };
      }

      return {
        result: data?.result || data?.detail || `Ошибка сервера (${response.status})`,
        error: true,
        status: response.status,
        isBanned: isIpBanned,
      };
    }

    return {
      result: data?.result !== undefined ? data.result : data,
      error: data?.error || false,
      status: response.status,
      isBanned: false,
    };
  } catch (err) {
    console.error(`API request error [${method} ${path}]:`, err);
    return {
      result: 'Ошибка соединения с сервером',
      error: true,
      status: 0,
      isBanned: false,
    };
  }
}

const GET = (path) => request('GET', path);
const POST = (path, body) => request('POST', path, body);
const PATCH = (path, body) => request('PATCH', path, body);

export const api = {
  // Users
  checkUser: (userId) =>
    GET(`/check_user?user_id=${userId}`),

  getUser: (userId) =>
    GET(`/get_user?user_id=${userId}`),

  addUser: ({ user_id, username, first_name, last_name, photo_url }) =>
    POST('/add_user', { user_id, username, first_name, last_name, photo_url }),

  // Cards
  getCard: (cardId) =>
    GET(`/get_card?card_id=${cardId}`),

  getRandomCards: (userId) =>
    GET(`/get_random_cards?user_id=${userId}`),

  selectChoice: (userId, cardId, choice) =>
    PATCH('/select_choice', { user_id: userId, card_id: cardId, choice }),

  addCard: (choiceA, choiceB, authorId) =>
    POST('/add_card', { choice_A: choiceA, choice_B: choiceB, author_id: authorId }),

  // Reactions
  likeCard: (userId, cardId) =>
    PATCH('/like_card', { user_id: userId, card_id: cardId }),

  dislikeCard: (userId, cardId) =>
    PATCH('/dislike_card', { user_id: userId, card_id: cardId }),

  // Comments
  addComment: (authorId, cardId, commentText) =>
    POST('/comment', { author_id: authorId, card_id: cardId, comment_text: commentText }),

  getComments: (cardId) =>
    GET(`/get_comments?card_id=${cardId}`),
};
