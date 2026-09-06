import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { DocumentList } from '../components/DocumentList';
import { DeleteConfirmModal } from '../components/DeleteConfirmModal';
import { ReplaceDocumentModal } from '../components/ReplaceDocumentModal';
import { listDocuments, deleteDocument, replaceDocument } from '../services/api';

describe('Document Management CRUD Component & Service Tests', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  const sampleDocuments = [
    {
      source: 'handbook_2026.pdf',
      file_type: '.pdf',
      chunk_count: 14,
      indexed_at: '2026-09-06T12:00:00Z',
    },
    {
      source: 'api_guidelines.txt',
      file_type: '.txt',
      chunk_count: 5,
      indexed_at: '2026-09-06T10:30:00Z',
    },
  ];

  // 1. Loading Skeleton
  it('1. DocumentList renders loading skeleton while fetching', () => {
    render(
      <DocumentList
        documents={[]}
        totalChunks={0}
        isLoading={true}
        onRefresh={vi.fn()}
        onDelete={vi.fn()}
        onReplace={vi.fn()}
      />
    );

    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('documents-table')).not.toBeInTheDocument();
  });

  // 2. Document Rows Rendering
  it('2. DocumentList renders document rows with names, badges, and chunk counts', () => {
    render(
      <DocumentList
        documents={sampleDocuments}
        totalChunks={19}
        isLoading={false}
        onRefresh={vi.fn()}
        onDelete={vi.fn()}
        onReplace={vi.fn()}
      />
    );

    expect(screen.getByTestId('documents-table')).toBeInTheDocument();
    expect(screen.getByText('handbook_2026.pdf')).toBeInTheDocument();
    expect(screen.getByText('14 chunks')).toBeInTheDocument();
    expect(screen.getByText('api_guidelines.txt')).toBeInTheDocument();
    expect(screen.getByText('5 chunks')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('TXT')).toBeInTheDocument();
  });

  // 3. Empty State
  it('3. DocumentList renders empty state when no documents exist', () => {
    render(
      <DocumentList
        documents={[]}
        totalChunks={0}
        isLoading={false}
        onRefresh={vi.fn()}
        onDelete={vi.fn()}
        onReplace={vi.fn()}
      />
    );

    expect(screen.getByTestId('empty-documents-state')).toBeInTheDocument();
    expect(screen.getByText('No documents indexed yet')).toBeInTheDocument();
  });

  // 4. Search Filtering
  it('4. DocumentList filters documents based on search input', () => {
    render(
      <DocumentList
        documents={sampleDocuments}
        totalChunks={19}
        isLoading={false}
        onRefresh={vi.fn()}
        onDelete={vi.fn()}
        onReplace={vi.fn()}
      />
    );

    const searchInput = screen.getByTestId('filter-docs-input');
    fireEvent.change(searchInput, { target: { value: 'handbook' } });

    expect(screen.getByText('handbook_2026.pdf')).toBeInTheDocument();
    expect(screen.queryByText('api_guidelines.txt')).not.toBeInTheDocument();

    // Clear filter
    const clearBtn = screen.getByLabelText('Clear filter');
    fireEvent.click(clearBtn);

    expect(screen.getByText('api_guidelines.txt')).toBeInTheDocument();
  });

  // 5. Error State
  it('5. DocumentList renders error message banner when error is provided', () => {
    render(
      <DocumentList
        documents={[]}
        totalChunks={0}
        isLoading={false}
        error="Failed to connect to backend service"
        onRefresh={vi.fn()}
        onDelete={vi.fn()}
        onReplace={vi.fn()}
      />
    );

    expect(screen.getByText('Failed to connect to backend service')).toBeInTheDocument();
  });

  // 6. Delete Confirmation Modal Opens
  it('6. Clicking delete button opens DeleteConfirmModal with document details', () => {
    render(
      <DocumentList
        documents={sampleDocuments}
        totalChunks={19}
        isLoading={false}
        onRefresh={vi.fn()}
        onDelete={vi.fn()}
        onReplace={vi.fn()}
      />
    );

    const deleteBtn = screen.getByTestId('delete-btn-handbook_2026.pdf');
    fireEvent.click(deleteBtn);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Delete Document' })).toBeInTheDocument();
    expect(screen.getByTestId('confirm-delete-btn')).toBeInTheDocument();
  });

  // 7. Cancel Delete Closes Modal
  it('7. Canceling delete modal closes it without calling delete callback', () => {
    const onDeleteMock = vi.fn();
    render(
      <DocumentList
        documents={sampleDocuments}
        totalChunks={19}
        isLoading={false}
        onRefresh={vi.fn()}
        onDelete={onDeleteMock}
        onReplace={vi.fn()}
      />
    );

    fireEvent.click(screen.getByTestId('delete-btn-handbook_2026.pdf'));
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    const cancelBtn = screen.getByText('Cancel');
    fireEvent.click(cancelBtn);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(onDeleteMock).not.toHaveBeenCalled();
  });

  // 8. Confirm Delete Calls Callback
  it('8. Confirming delete calls delete handler with document source', async () => {
    const onDeleteMock = vi.fn().mockResolvedValue({ source: 'handbook_2026.pdf', chunks_deleted: 14 });
    render(
      <DocumentList
        documents={sampleDocuments}
        totalChunks={19}
        isLoading={false}
        onRefresh={vi.fn()}
        onDelete={onDeleteMock}
        onReplace={vi.fn()}
      />
    );

    fireEvent.click(screen.getByTestId('delete-btn-handbook_2026.pdf'));
    const confirmBtn = screen.getByTestId('confirm-delete-btn');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(onDeleteMock).toHaveBeenCalledWith('handbook_2026.pdf');
    });
  });

  // 9. Replace Modal Opens
  it('9. Clicking replace button opens ReplaceDocumentModal', () => {
    render(
      <DocumentList
        documents={sampleDocuments}
        totalChunks={19}
        isLoading={false}
        onRefresh={vi.fn()}
        onDelete={vi.fn()}
        onReplace={vi.fn()}
      />
    );

    const replaceBtn = screen.getByTestId('replace-btn-handbook_2026.pdf');
    fireEvent.click(replaceBtn);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Replace & Re-index' })).toBeInTheDocument();
  });

  // 10. Replace Modal Validates File Extension
  it('10. Replace modal rejects invalid file format client-side', () => {
    const onConfirmMock = vi.fn();
    render(
      <ReplaceDocumentModal
        isOpen={true}
        document={sampleDocuments[0]}
        onConfirm={onConfirmMock}
        onClose={vi.fn()}
        isReplacing={false}
      />
    );

    const input = screen.getByTestId('replace-file-input');
    const invalidFile = new File(['binary'], 'script.sh', { type: 'application/x-sh' });
    fireEvent.change(input, { target: { files: [invalidFile] } });

    expect(screen.getByText('Unsupported format. Only PDF, TXT, and Markdown are supported.')).toBeInTheDocument();
    expect(onConfirmMock).not.toHaveBeenCalled();
  });

  // 11. Refresh Button Calls onRefresh
  it('11. Clicking refresh button triggers onRefresh callback', () => {
    const onRefreshMock = vi.fn();
    render(
      <DocumentList
        documents={sampleDocuments}
        totalChunks={19}
        isLoading={false}
        onRefresh={onRefreshMock}
        onDelete={vi.fn()}
        onReplace={vi.fn()}
      />
    );

    const refreshBtn = screen.getByTestId('refresh-docs-btn');
    fireEvent.click(refreshBtn);

    expect(onRefreshMock).toHaveBeenCalledTimes(1);
  });

  // 12. API Client Functions (listDocuments, deleteDocument, replaceDocument)
  it('12. API functions listDocuments, deleteDocument, replaceDocument execute proper HTTP requests', async () => {
    // 12a. listDocuments
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ documents: sampleDocuments, total_chunks: 19 }),
    });

    const listResult = await listDocuments();
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/documents'));
    expect(listResult.documents).toHaveLength(2);

    // 12b. deleteDocument
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ source: 'handbook_2026.pdf', chunks_deleted: 14, status: 'deleted' }),
    });

    const deleteResult = await deleteDocument('handbook_2026.pdf');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/documents/handbook_2026.pdf'),
      expect.objectContaining({ method: 'DELETE' })
    );
    expect(deleteResult.status).toBe('deleted');

    // 12c. replaceDocument
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ filename: 'updated.pdf', chunks_created: 15, status: 'success' }),
    });

    const file = new File(['content'], 'updated.pdf', { type: 'application/pdf' });
    const replaceResult = await replaceDocument('handbook_2026.pdf', file);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/documents/handbook_2026.pdf'),
      expect.objectContaining({ method: 'PUT' })
    );
    expect(replaceResult.status).toBe('success');
  });
});
