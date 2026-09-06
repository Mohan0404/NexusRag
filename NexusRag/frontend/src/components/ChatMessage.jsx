import React from 'react';
import SourceCard from './SourceCard';
import { formatTime } from '../utils/helpers';

/**
 * Message bubble component displaying user queries and grounded assistant answers.
 */
export function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const isError = message.isError;
  const sources = message.sources || [];

  return (
    <div
      className={`message-wrapper ${isUser ? 'message-user' : 'message-assistant'}`}
      data-testid={`chat-message-${message.role}`}
    >
      {!isUser && (
        <div className="avatar avatar-assistant" aria-hidden="true">
          AI
        </div>
      )}

      <div className={`bubble ${isUser ? 'bubble-user' : 'bubble-assistant'} ${isError ? 'bubble-error' : ''}`}>
        <div className="message-content" style={{ whiteSpace: 'pre-wrap' }}>
          {message.content}
        </div>

        {/* Source Citations */}
        {!isUser && sources.length > 0 && (
          <div className="sources-container" data-testid="sources-container">
            <div className="sources-header">
              <span>Sources ({sources.length})</span>
            </div>
            <div className="sources-list">
              {sources.map((src, idx) => (
                <SourceCard key={`${src.source}-${src.page || idx}-${idx}`} source={src} />
              ))}
            </div>
          </div>
        )}

        <div className="message-meta">
          <span>{formatTime(message.timestamp)}</span>
          {!isUser && message.model && <span>• {message.model.split('/').pop()}</span>}
        </div>
      </div>

      {isUser && (
        <div className="avatar avatar-user" aria-hidden="true">
          You
        </div>
      )}
    </div>
  );
}

export default ChatMessage;
