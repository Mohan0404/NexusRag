import React, { useState, useRef, useEffect } from 'react';

const MAX_CHARS = 2000;

/**
 * Modern integrated chat composer with auto-expanding textarea, character counter,
 * keyboard shortcuts hint, and Enter-to-submit behavior.
 */
export function ChatInput({ onSendMessage, isLoading = false }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const trimmed = text.trim();
  const isValid = trimmed.length > 0 && text.length <= MAX_CHARS;

  // Auto-resize textarea height based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(Math.max(textareaRef.current.scrollHeight, 44), 180)}px`;
    }
  }, [text]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!isValid || isLoading) return;

    onSendMessage(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form
      className="chat-input-form"
      onSubmit={handleSubmit}
      role="search"
      aria-label="Ask a question"
      data-testid="chat-input-form"
    >
      <div className="chat-composer-card">
        <label htmlFor="chat-textarea" className="sr-only" style={{ display: 'none' }}>
          Ask a question about your documents
        </label>
        <textarea
          id="chat-textarea"
          ref={textareaRef}
          className="chat-textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents... (Shift+Enter for newline)"
          rows={1}
          maxLength={MAX_CHARS}
          disabled={isLoading}
          aria-label="Ask a question about your documents"
          data-testid="chat-input-textarea"
        />

        <div className="chat-composer-footer">
          <div className="chat-composer-hints">
            <span className="input-hint">Shift+Enter for newline</span>
            <span className="hint-separator">•</span>
            <span className={`char-counter ${text.length > MAX_CHARS ? 'char-limit-exceeded' : ''}`}>
              {text.length}/{MAX_CHARS}
            </span>
          </div>

          <button
            type="submit"
            className="chat-submit-btn"
            disabled={!isValid || isLoading}
            aria-label="Send question"
            data-testid="chat-submit-btn"
          >
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
            <span className="submit-label">Send</span>
          </button>
        </div>
      </div>
    </form>
  );
}

export default ChatInput;
