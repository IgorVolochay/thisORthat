/**
 * API service — all backend requests for This OR That.
 * All endpoints return { result, error } (BaseResponse).
 */

const BASE_URL = process.env.REACT_APP_API_URL || '/api';

async function request(method, path, body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${BASE_URL}${path}`, options);
  const data = await response.json();
  return data;
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

  // TODO: GET /get_comments — endpoint not yet implemented on backend
  getComments: (cardId) => {
    console.warn('GET /get_comments not implemented on backend yet');
    return Promise.resolve({ result: [], error: false });
  },
};
