import React from 'react';

/**
 * Animated pulsating loading indicator for pending RAG queries.
 */
export function LoadingIndicator({ text = 'Searching knowledge base & generating answer...' }) {
  return (
    <div className="loading-indicator" role="status" aria-live="polite" data-testid="loading-indicator">
      <div className="dots-pulse" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <span className="loading-text">{text}</span>
    </div>
  );
}

export default LoadingIndicator;
