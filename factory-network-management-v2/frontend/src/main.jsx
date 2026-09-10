import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/theme.css';

// Optional, user-supplied font: absent files never generate a broken request.
const fonts = import.meta.glob('./assets/fonts/SF Distant Galaxy.ttf', { eager: true, query: '?url', import: 'default' });
const fontUrl = Object.values(fonts)[0];
if (fontUrl) {
  const face = new FontFace('SF Distant Galaxy', `url("${fontUrl}")`);
  face.load().then((loaded) => document.fonts.add(loaded)).catch(() => {});
}

ReactDOM.createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>);
