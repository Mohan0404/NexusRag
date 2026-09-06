import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import LoadingIndicator from './LoadingIndicator';

const SUGGESTIONS = [
  "What is our company's remote work policy?",
  "Summarize the annual leave procedure.",
  "How do I submit an expense report?",
];

/**
 * Scrollable chat viewport showing messages, loading indicators, and empty state chips.
 */
export function ChatWindow({ messages = [], isLoading = false, onSelectSuggestion }) {
  const bottomRef = useRef(null);

  // Auto-scroll to bottom when messages or loading state changes
  useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  return (
    <div className="chat-window" role="log" aria-live="polite" data-testid="chat-window">
      {messages.length === 0 ? (
        <div className="chat-empty" data-testid="chat-empty-state">
          <div className="empty-icon" aria-hidden="true">
            💬
          </div>
          <h2 className="empty-title">Welcome to NexusRAG</h2>
          <p className="empty-desc">
            Ask any question grounded strictly in your indexed enterprise documents. Answers include direct
            source citations with page numbers.
          </p>

          <div className="empty-suggestions">
            {SUGGESTIONS.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                className="suggestion-chip"
                onClick={() => onSelectSuggestion && onSelectSuggestion(prompt)}
                data-testid={`suggestion-chip-${idx}`}
              >
                💡 {prompt}
              </button>
            ))}
          </div>
        </div>
      ) : (
        messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
      )}

      {isLoading && <LoadingIndicator />}
      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
}

export default ChatWindow;
