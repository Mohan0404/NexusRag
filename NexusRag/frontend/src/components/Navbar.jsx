import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { checkHealth } from '../services/api';
import { useConversation } from '../context/ConversationContext';

/**
 * Top navigation bar with routing links, health status indicator, and
 * a "+ New Chat" button that creates a new empty conversation.
 */
export function Navbar() {
  const [healthStatus, setHealthStatus] = useState('checking'); // 'connected' | 'offline' | 'checking'
  const { createNewConversation } = useConversation();

  // Perform a simple health check once when the navbar mounts. Do NOT poll.
  useEffect(() => {
    let isMounted = true;

    async function fetchHealth() {
      try {
        await checkHealth();
        if (isMounted) setHealthStatus('connected');
      } catch {
        if (isMounted) setHealthStatus('offline');
      }
    }

    fetchHealth();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <header className="navbar" role="banner">
      <NavLink to="/chat" className="nav-brand" aria-label="NexusRAG Home">
        <span className="brand-icon" aria-hidden="true">
          ⚡
        </span>
        <span className="brand-title">NexusRAG</span>
        <span className="brand-badge">Assistant</span>
      </NavLink>

      <nav className="nav-links" role="navigation" aria-label="Main Navigation">
        <NavLink
          to="/chat"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          data-testid="nav-chat-link"
        >
          Chat
        </NavLink>
        <NavLink
          to="/documents"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          data-testid="nav-documents-link"
        >
          Documents
        </NavLink>

        <button
          type="button"
          className="btn-new-chat"
          onClick={createNewConversation}
          aria-label="Start a new chat conversation"
          data-testid="new-chat-btn"
        >
          + New Chat
        </button>
      </nav>

      <div className="nav-status" aria-label={`Backend server status: ${healthStatus}`}>
        <span
          className={`status-dot ${healthStatus === 'connected' ? 'status-connected' : 'status-offline'}`}
          data-testid="status-dot"
        />
        <span className="status-label" data-testid="status-label">
          {healthStatus === 'connected' ? 'Connected' : healthStatus === 'offline' ? 'Offline' : 'Checking...'}
        </span>
      </div>
    </header>
  );
}

export default Navbar;
