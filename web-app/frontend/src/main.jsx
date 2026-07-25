import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';

// Nếu đã tạo file src/index.css thì giữ nguyên, nếu chưa có thì comment dòng dưới lại nhé
// import './index.css'; 

// Dùng trực tiếp createRoot đã import ở trên
createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);