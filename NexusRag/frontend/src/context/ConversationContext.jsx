import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';

/**
 * localStorage key for chat history. Versioned to allow future migrations.
 */
const STORAGE_KEY = 'nexusrag:chat-history:v1';

/**
 * Generate a simple unique id without external dependencies.
 */
function generateId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * Create a new empty conversation object.
 *
 * @param {string} [id] - Optional id; generated if omitted.
 * @returns {Conversation}
 */
function createConversation(id) {
  const now = new Date().toISOString();
  return {
    id: id || generateId(),
    title: 'New Chat',
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

/**
 * Derive a short human-readable title from the first user question.
 * Deterministic, no network call.
 *
 * @param {string} question
 * @returns {string}
 */
export function deriveTitle(question) {
  const trimmed = (question || '').trim();
  if (!trimmed) return 'New Chat';
  // Take first 6 words, cap at 60 characters
  const words = trimmed.split(/\s+/).slice(0, 6).join(' ');
  return words.length > 60 ? words.slice(0, 60) : words;
}

/**
 * Read and validate the persisted state from localStorage.
 * Falls back to a single empty conversation on any parse error.
 *
 * @returns {{ conversations: Conversation[], activeConversationId: string }}
 */
function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);

    // Validate minimum required structure
    if (
      !parsed ||
      !Array.isArray(parsed.conversations) ||
      parsed.conversations.length === 0 ||
      typeof parsed.activeConversationId !== 'string'
    ) {
      return null;
    }

    // Ensure every conversation has required fields
    const valid = parsed.conversations.every(
      (c) =>
        c &&
        typeof c.id === 'string' &&
        typeof c.title === 'string' &&
        Array.isArray(c.messages)
    );

    if (!valid) return null;

    return parsed;
  } catch {
    return null;
  }
}

/**
 * Persist the current state to localStorage.
 * Silently swallows storage errors (e.g. private mode quota).
 */
function saveToStorage(conversations, activeConversationId) {
  try {
    // Strip loading state — messages are already clean in context
    const payload = JSON.stringify({ conversations, activeConversationId });
    localStorage.setItem(STORAGE_KEY, payload);
  } catch {
    // Storage quota or private mode — silently ignore
  }
}

/**
 * Build the initial conversation state:
 * restore from localStorage or create a fresh empty conversation.
 */
function buildInitialState() {
  const stored = loadFromStorage();
  if (!stored) {
    const conv = createConversation();
    return { conversations: [conv], activeConversationId: conv.id };
  }

  const { conversations, activeConversationId } = stored;

  // If stored activeId no longer exists in the list, fall back to the first
  const idExists = conversations.some((c) => c.id === activeConversationId);
  return {
    conversations,
    activeConversationId: idExists ? activeConversationId : conversations[0].id,
  };
}

const ConversationContext = createContext(null);

/**
 * Provider that owns all conversation state and localStorage persistence.
 */
export function ConversationProvider({ children }) {
  const [{ conversations, activeConversationId }, setState] = useState(buildInitialState);

  // Ref to track whether we should skip the initial save (we already loaded it)
  const isFirstRender = useRef(true);

  // Persist to localStorage whenever state changes (but not on first render)
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    saveToStorage(conversations, activeConversationId);
  }, [conversations, activeConversationId]);

  /** Return the currently active conversation object or null. */
  const activeConversation = conversations.find((c) => c.id === activeConversationId) || null;

  /**
   * Create and activate a new empty conversation.
   * If the current active conversation is already empty, does nothing.
   */
  const createNewConversation = useCallback(() => {
    setState((prev) => {
      const current = prev.conversations.find((c) => c.id === prev.activeConversationId);
      // Guard: do not create a duplicate empty conversation
      if (current && current.messages.length === 0) {
        return prev;
      }
      const newConv = createConversation();
      return {
        conversations: [...prev.conversations, newConv],
        activeConversationId: newConv.id,
      };
    });
  }, []);

  /**
   * Switch to a specific conversation by id.
   *
   * @param {string} id
   */
  const setActiveConversation = useCallback((id) => {
    setState((prev) => {
      const exists = prev.conversations.some((c) => c.id === id);
      if (!exists) return prev;
      return { ...prev, activeConversationId: id };
    });
  }, []);

  /**
   * Append a fully-formed message object to the active conversation.
   * Loading state (isLoading) is intentionally NOT stored here.
   *
   * @param {object} message
   */
  const appendMessage = useCallback((message) => {
    setState((prev) => {
      const now = new Date().toISOString();
      const updated = prev.conversations.map((c) => {
        if (c.id !== prev.activeConversationId) return c;
        return {
          ...c,
          messages: [...c.messages, message],
          updatedAt: now,
        };
      });
      return { conversations: updated, activeConversationId: prev.activeConversationId };
    });
  }, []);

  /**
   * Update the title of a specific conversation.
   *
   * @param {string} convId
   * @param {string} title
   */
  const updateConversationTitle = useCallback((convId, title) => {
    setState((prev) => {
      const updated = prev.conversations.map((c) => {
        if (c.id !== convId) return c;
        return { ...c, title };
      });
      return { conversations: updated, activeConversationId: prev.activeConversationId };
    });
  }, []);

  const value = {
    conversations,
    activeConversationId,
    activeConversation,
    createNewConversation,
    setActiveConversation,
    appendMessage,
    updateConversationTitle,
  };

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
}

/**
 * Hook to consume the ConversationContext.
 * Must be used inside <ConversationProvider>.
 */
export function useConversation() {
  const ctx = useContext(ConversationContext);
  if (!ctx) {
    throw new Error('useConversation must be used within a ConversationProvider');
  }
  return ctx;
}

export default ConversationContext;
