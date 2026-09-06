import { useState, useCallback } from 'react';
import { sendChatMessage } from '../services/api';
import { useConversation, deriveTitle } from '../context/ConversationContext';

/**
 * Custom hook for managing RAG chat state and interactions.
 *
 * Messages are stored in ConversationContext (backed by localStorage) so they
 * survive unmount/remount (navigation away from ChatPage and back).
 *
 * Ephemeral state (isLoading, error) lives only in local React state and is
 * intentionally NOT persisted to localStorage.
 */
export function useChat() {
  const {
    activeConversation,
    activeConversationId,
    appendMessage,
    updateConversationTitle,
  } = useConversation();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Derive messages from the active conversation (persisted)
  const messages = activeConversation ? activeConversation.messages : [];

  /**
   * Submits a user question to the RAG pipeline.
   *
   * @param {string} rawQuestion - Unprocessed user input.
   */
  const sendMessage = useCallback(
    async (rawQuestion) => {
      const question = (rawQuestion || '').trim();

      if (!question) {
        setError('Please enter a valid question.');
        return;
      }

      if (question.length > 2000) {
        setError('Question exceeds maximum allowed length of 2,000 characters.');
        return;
      }

      // Append user message immediately and persist via context
      const userMessage = {
        id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: 'user',
        content: question,
        timestamp: new Date().toISOString(),
      };

      appendMessage(userMessage);

      // Auto-generate conversation title from the first user question
      if (activeConversation && activeConversation.messages.length === 0) {
        updateConversationTitle(activeConversationId, deriveTitle(question));
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await sendChatMessage(question);

        const assistantMessage = {
          id: `assistant-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: response.answer,
          sources: response.sources || [],
          model: response.model,
          context_chunks_used: response.context_chunks_used,
          timestamp: new Date().toISOString(),
        };

        appendMessage(assistantMessage);
      } catch (err) {
        const errorMessage = err.message || 'Failed to generate answer. Please try again.';
        setError(errorMessage);

        // Also append an error bubble so the user sees feedback inside the conversation flow
        const errorResponse = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `Error: ${errorMessage}`,
          isError: true,
          sources: [],
          timestamp: new Date().toISOString(),
        };
        appendMessage(errorResponse);
      } finally {
        setIsLoading(false);
      }
    },
    [activeConversation, activeConversationId, appendMessage, updateConversationTitle]
  );

  /**
   * Clears the error banner. Does not clear conversation messages —
   * use createNewConversation() in ConversationContext for that.
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearError,
  };
}
