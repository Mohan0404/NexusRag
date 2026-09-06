import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import ChatPage from './pages/ChatPage';
import DocumentsPage from './pages/DocumentsPage';
import { ConversationProvider } from './context/ConversationContext';

/**
 * Root application shell providing navigation and view routing.
 * ConversationProvider wraps the Routes so conversation state (backed by
 * localStorage) survives route changes when ChatPage unmounts.
 */
export function App() {
  return (
    <ConversationProvider>
      <div className="app-container">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="*" element={<Navigate to="/chat" replace />} />
          </Routes>
        </main>
      </div>
    </ConversationProvider>
  );
}

export default App;
