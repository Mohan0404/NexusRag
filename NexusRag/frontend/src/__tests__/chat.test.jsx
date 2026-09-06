import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import Navbar from '../components/Navbar';
import ChatPage from '../pages/ChatPage';
import ChatInput from '../components/ChatInput';
import { ConversationProvider } from '../context/ConversationContext';

/**
 * Helper: render a component that requires ConversationProvider + MemoryRouter.
 */
function renderWithProviders(ui, { initialEntries = ['/chat'] } = {}) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <ConversationProvider>{ui}</ConversationProvider>
    </MemoryRouter>
  );
}

describe('Chat & Navbar Component Tests', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    localStorage.clear();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    localStorage.clear();
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  // ===================================================================
  // 1. Navbar Renders
  // ===================================================================
  it('1. Navbar renders brand title and navigation links', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ status: 'healthy' }),
    });

    renderWithProviders(<Navbar />);

    expect(screen.getByText('NexusRAG')).toBeInTheDocument();
    expect(screen.getByTestId('nav-chat-link')).toBeInTheDocument();
    expect(screen.getByTestId('nav-documents-link')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId('status-label')).toHaveTextContent('Connected');
    });
  });

  // ===================================================================
  // 18. Health Connected
  // ===================================================================
  it('18. Navbar shows Connected status when health check succeeds', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ status: 'healthy' }),
    });

    renderWithProviders(<Navbar />);

    await waitFor(() => {
      expect(screen.getByTestId('status-label')).toHaveTextContent('Connected');
    });
    expect(screen.getByTestId('status-dot')).toHaveClass('status-connected');
  });

  // ===================================================================
  // 19. Health Offline
  // ===================================================================
  it('19. Navbar shows Offline status when health check fails', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    renderWithProviders(<Navbar />);

    await waitFor(() => {
      expect(screen.getByTestId('status-label')).toHaveTextContent('Offline');
    });
    expect(screen.getByTestId('status-dot')).toHaveClass('status-offline');
  });

  // ===================================================================
  // 2. Chat Input Renders
  // ===================================================================
  it('2. Chat input renders textarea and submit button', () => {
    render(<ChatInput onSendMessage={vi.fn()} isLoading={false} />);

    expect(screen.getByTestId('chat-input-textarea')).toBeInTheDocument();
    expect(screen.getByTestId('chat-submit-btn')).toBeInTheDocument();
    expect(screen.getByText('0/2000')).toBeInTheDocument();
  });

  // ===================================================================
  // 3. Empty Input Disables Submit
  // ===================================================================
  it('3. Empty or whitespace-only input disables submit button', () => {
    render(<ChatInput onSendMessage={vi.fn()} isLoading={false} />);

    const submitBtn = screen.getByTestId('chat-submit-btn');
    const textarea = screen.getByTestId('chat-input-textarea');

    // Initially empty
    expect(submitBtn).toBeDisabled();

    // Whitespace only
    fireEvent.change(textarea, { target: { value: '    ' } });
    expect(submitBtn).toBeDisabled();
  });

  // ===================================================================
  // 4. User Can Type Question
  // ===================================================================
  it('4. User can type a question and character count updates', () => {
    render(<ChatInput onSendMessage={vi.fn()} isLoading={false} />);

    const textarea = screen.getByTestId('chat-input-textarea');
    const submitBtn = screen.getByTestId('chat-submit-btn');

    fireEvent.change(textarea, { target: { value: 'What is the leave policy?' } });

    expect(textarea.value).toBe('What is the leave policy?');
    expect(screen.getByText('25/2000')).toBeInTheDocument();
    expect(submitBtn).toBeEnabled();
  });

  // ===================================================================
  // 5. Enter Submits
  // ===================================================================
  it('5. Pressing Enter triggers submission', () => {
    const handleSend = vi.fn();
    render(<ChatInput onSendMessage={handleSend} isLoading={false} />);

    const textarea = screen.getByTestId('chat-input-textarea');

    fireEvent.change(textarea, { target: { value: 'Can I work remotely?' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: false });

    expect(handleSend).toHaveBeenCalledWith('Can I work remotely?');
    expect(textarea.value).toBe('');
  });

  // ===================================================================
  // 6 & 7. Assistant Response & Source Citations Render
  // ===================================================================
  it('6 & 7. Assistant response and source citations render correctly', async () => {
    const mockChatResponse = {
      answer: 'Employees receive 25 annual leave days per calendar year.',
      sources: [
        {
          source: 'handbook_2026.pdf',
          file_type: '.pdf',
          page: 14,
        },
      ],
      query: 'What is the leave policy?',
      model: 'google/gemini-2.5-flash',
      context_chunks_used: 2,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockChatResponse,
    });

    renderWithProviders(<ChatPage />);

    const textarea = screen.getByTestId('chat-input-textarea');
    const submitBtn = screen.getByTestId('chat-submit-btn');

    fireEvent.change(textarea, { target: { value: 'What is the leave policy?' } });
    fireEvent.click(submitBtn);

    // User message should appear
    expect(screen.getByText('What is the leave policy?')).toBeInTheDocument();

    // Assistant response should appear
    await waitFor(() => {
      expect(
        screen.getByText('Employees receive 25 annual leave days per calendar year.')
      ).toBeInTheDocument();
    });

    // Citations should appear
    expect(screen.getByText('Sources (1)')).toBeInTheDocument();
    expect(screen.getByText('handbook_2026.pdf')).toBeInTheDocument();
    expect(screen.getByText('Page 14')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
  });

  // ===================================================================
  // 8. Loading State Renders
  // ===================================================================
  it('8. Loading indicator renders while question is being answered', async () => {
    let resolvePromise;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    global.fetch.mockReturnValueOnce(pendingPromise);

    renderWithProviders(<ChatPage />);

    const textarea = screen.getByTestId('chat-input-textarea');
    const submitBtn = screen.getByTestId('chat-submit-btn');

    fireEvent.change(textarea, { target: { value: 'How do expense claims work?' } });
    fireEvent.click(submitBtn);

    // Loading indicator must be visible while promise is pending
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
    expect(submitBtn).toBeDisabled();

    // Resolve promise
    await act(async () => {
      resolvePromise({
        ok: true,
        status: 200,
        json: async () => ({
          answer: 'Submit via the portal.',
          sources: [],
          query: 'How do expense claims work?',
          model: 'test',
          context_chunks_used: 1,
        }),
      });
    });

    await waitFor(() => {
      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
      expect(screen.getByText('Submit via the portal.')).toBeInTheDocument();
    });
  });

  // ===================================================================
  // 9. API Error Renders (500)
  // ===================================================================
  it('9. Internal server error (500) renders user-friendly error message', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Database query timeout' }),
    });

    renderWithProviders(<ChatPage />);

    const textarea = screen.getByTestId('chat-input-textarea');
    const submitBtn = screen.getByTestId('chat-submit-btn');

    fireEvent.change(textarea, { target: { value: 'Search failed query' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId('chat-error-banner')).toHaveTextContent(
        'An internal server error occurred while processing your question.'
      );
    });
  });

  // ===================================================================
  // 10. 502 Error Renders Useful Message
  // ===================================================================
  it('10. Upstream provider outage (502) renders specific provider message', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 502,
      json: async () => ({
        detail: 'LLM generation provider temporarily unavailable. Please retry shortly.',
      }),
    });

    renderWithProviders(<ChatPage />);

    const textarea = screen.getByTestId('chat-input-textarea');
    const submitBtn = screen.getByTestId('chat-submit-btn');

    fireEvent.change(textarea, { target: { value: 'Provider failing question' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId('chat-error-banner')).toHaveTextContent(
        'The AI service is temporarily unavailable. Please try again shortly.'
      );
    });
  });
});
