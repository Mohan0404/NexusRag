import React from 'react';

/**
 * Visual empty state displayed when no documents are indexed or found.
 */
export function EmptyDocumentState({ isFiltered = false, onResetFilter }) {
  return (
    <div className="empty-documents-container" data-testid="empty-documents-state">
      <div className="empty-documents-icon">
        <svg
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
      </div>
      <h3 className="empty-documents-title">
        {isFiltered ? 'No matching documents' : 'No documents indexed yet'}
      </h3>
      <p className="empty-documents-desc">
        {isFiltered
          ? 'Try adjusting your search query or clear the filter.'
          : 'Upload PDF, TXT, or Markdown documents on the right to start building your AI knowledge base.'}
      </p>
      {isFiltered && onResetFilter && (
        <button
          type="button"
          className="btn-secondary btn-sm"
          onClick={onResetFilter}
        >
          Clear Filter
        </button>
      )}
    </div>
  );
}
