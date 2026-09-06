import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

describe('Frontend Routing & Navigation Tests', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    localStorage.clear();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'healthy' }),
    });
  });

  afterEach(() => {
    localStorage.clear();
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('1. Renders ChatPage when navigating to /chat', async () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId('chat-input-textarea')).toBeInTheDocument();
    expect(screen.getByTestId('chat-submit-btn')).toBeInTheDocument();
  });

  it('2. Renders DocumentsPage when navigating to /documents', async () => {
    render(
      <MemoryRouter initialEntries={['/documents']}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId('documents-page')).toBeInTheDocument();
    expect(screen.getByTestId('drop-zone')).toBeInTheDocument();
    expect(screen.getByText('Knowledge Base Documents')).toBeInTheDocument();
  });

  it('3. Redirects root path / to /chat by default', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    // Should redirect to /chat and show chat input
    expect(screen.getByTestId('chat-input-textarea')).toBeInTheDocument();
  });

  it('4. Navigates between Chat and Documents via Navbar links', async () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <App />
      </MemoryRouter>
    );

    // Initially on chat
    expect(screen.getByTestId('chat-input-textarea')).toBeInTheDocument();

    // Click navigation link to Documents
    const docsLink = screen.getByTestId('nav-documents-link');
    fireEvent.click(docsLink);

    // Expect DocumentsPage to be rendered
    await waitFor(() => {
      expect(screen.getByTestId('drop-zone')).toBeInTheDocument();
    });

    // Click navigation link back to Chat
    const chatLink = screen.getByTestId('nav-chat-link');
    fireEvent.click(chatLink);

    // Expect ChatPage to be rendered again
    await waitFor(() => {
      expect(screen.getByTestId('chat-input-textarea')).toBeInTheDocument();
    });
  });
});
