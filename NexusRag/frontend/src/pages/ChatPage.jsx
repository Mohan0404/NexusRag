import React from 'react';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';
import { useChat } from '../hooks/useChat';

/**
 * Chat page view orchestrating conversation stream and user input.
 *
 * Messages are now sourced from ConversationContext (via useChat), so they
 * survive navigation away from and back to this page.
 */
export function ChatPage() {
  const { messages, isLoading, error, sendMessage } = useChat();

  const handleSelectSuggestion = (prompt) => {
    sendMessage(prompt);
  };

  return (
    <div className="chat-page" data-testid="chat-page">
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        onSelectSuggestion={handleSelectSuggestion}
      />

      {error && (
        <div className="error-banner" role="alert" data-testid="chat-error-banner">
          <span>⚠️ {error}</span>
        </div>
      )}

      <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
    </div>
  );
}

export default ChatPage;
