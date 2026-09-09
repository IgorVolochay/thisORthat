import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

test('renders app without crashing', async () => {
  const container = document.createElement('div');
  document.body.appendChild(container);
  
  await act(async () => {
    const root = createRoot(container);
    root.render(<App />);
  });

  expect(container.innerHTML).toBeTruthy();
});
