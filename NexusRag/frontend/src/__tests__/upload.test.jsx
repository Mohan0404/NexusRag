import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import DocumentUploader from '../components/DocumentUploader';

describe('Document Upload Component Tests', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  // ===================================================================
  // 11. Upload Component Renders
  // ===================================================================
  it('11. DocumentUploader renders drop zone and format badges', () => {
    render(
      <MemoryRouter>
        <DocumentUploader />
      </MemoryRouter>
    );

    expect(screen.getByTestId('document-uploader')).toBeInTheDocument();
    expect(screen.getByTestId('drop-zone')).toBeInTheDocument();
    expect(screen.getByText('PDF (.pdf)')).toBeInTheDocument();
    expect(screen.getByText('Text (.txt)')).toBeInTheDocument();
    expect(screen.getByText('Markdown (.md)')).toBeInTheDocument();
  });

  // ===================================================================
  // 12. Unsupported Extension Rejected
  // ===================================================================
  it('12. Unsupported file extension (.exe) is rejected client-side', () => {
    render(
      <MemoryRouter>
        <DocumentUploader />
      </MemoryRouter>
    );

    const input = screen.getByTestId('file-upload-input');
    const invalidFile = new File(['content'], 'malicious.exe', { type: 'application/x-msdownload' });

    fireEvent.change(input, { target: { files: [invalidFile] } });

    expect(screen.getByTestId('upload-error-banner')).toHaveTextContent(
      "Unsupported file format '.exe'"
    );
    expect(screen.queryByTestId('upload-submit-btn')).not.toBeInTheDocument();
  });

  // ===================================================================
  // 13. File > 10 MB Rejected
  // ===================================================================
  it('13. File exceeding 10 MB limit is rejected client-side', () => {
    render(
      <MemoryRouter>
        <DocumentUploader />
      </MemoryRouter>
    );

    const input = screen.getByTestId('file-upload-input');
    // 11 MB file
    const oversizedFile = new File(['x'.repeat(100)], 'huge.pdf', { type: 'application/pdf' });
    Object.defineProperty(oversizedFile, 'size', { value: 11 * 1024 * 1024 });

    fireEvent.change(input, { target: { files: [oversizedFile] } });

    expect(screen.getByTestId('upload-error-banner')).toHaveTextContent(
      'File exceeds the maximum size limit of 10 MB'
    );
    expect(screen.queryByTestId('upload-submit-btn')).not.toBeInTheDocument();
  });

  // ===================================================================
  // 14. Empty File Rejected
  // ===================================================================
  it('14. Zero-byte file is rejected client-side', () => {
    render(
      <MemoryRouter>
        <DocumentUploader />
      </MemoryRouter>
    );

    const input = screen.getByTestId('file-upload-input');
    const emptyFile = new File([], 'empty.txt', { type: 'text/plain' });

    fireEvent.change(input, { target: { files: [emptyFile] } });

    expect(screen.getByTestId('upload-error-banner')).toHaveTextContent(
      'The selected file is empty (0 bytes)'
    );
  });

  // ===================================================================
  // 15 & 16. FormData Upload Triggered & Success Displays Chunks
  // ===================================================================
  it('15 & 16. Valid upload sends FormData and displays chunk count on success', async () => {
    const mockUploadResponse = {
      filename: 'company_policy.pdf',
      file_type: '.pdf',
      file_size_bytes: 2048,
      chunks_created: 14,
      status: 'success',
      message: "Successfully ingested and indexed 'company_policy.pdf' (14 chunks).",
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockUploadResponse,
    });

    render(
      <MemoryRouter>
        <DocumentUploader />
      </MemoryRouter>
    );

    const input = screen.getByTestId('file-upload-input');
    const validFile = new File(['valid content here'], 'company_policy.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(input, { target: { files: [validFile] } });

    // File selected state
    expect(screen.getByText('company_policy.pdf')).toBeInTheDocument();
    const uploadBtn = screen.getByTestId('upload-submit-btn');

    // Click upload
    fireEvent.click(uploadBtn);

    // Verify fetch call was made with FormData
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toContain('/documents/upload');
    expect(options.method).toBe('POST');
    expect(options.body).toBeInstanceOf(FormData);

    // Verify success UI
    await waitFor(() => {
      expect(screen.getByTestId('upload-success-card')).toBeInTheDocument();
    });

    expect(screen.getByText(/Indexed successfully/i)).toBeInTheDocument();
    expect(screen.getByText('14')).toBeInTheDocument();
    expect(screen.getByTestId('go-to-chat-btn')).toBeInTheDocument();
  });

  // ===================================================================
  // 17. Upload Error Displays Useful Message
  // ===================================================================
  it('17. Server error during upload displays user-friendly error message', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 413,
      json: async () => ({
        detail: 'File size exceeds maximum allowed limit of 10 MB.',
      }),
    });

    render(
      <MemoryRouter>
        <DocumentUploader />
      </MemoryRouter>
    );

    const input = screen.getByTestId('file-upload-input');
    const validFile = new File(['sample'], 'guide.md', { type: 'text/markdown' });

    fireEvent.change(input, { target: { files: [validFile] } });
    fireEvent.click(screen.getByTestId('upload-submit-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('upload-error-banner')).toHaveTextContent(
        'File size exceeds maximum allowed limit of 10 MB.'
      );
    });
  });
});
