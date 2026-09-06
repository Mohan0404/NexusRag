import React, { useState, useMemo } from 'react';
import { DocumentRow } from './DocumentRow';
import { EmptyDocumentState } from './EmptyDocumentState';
import { DeleteConfirmModal } from './DeleteConfirmModal';
import { ReplaceDocumentModal } from './ReplaceDocumentModal';

/**
 * Main Document Management Table with search filter, statistics, and CRUD modals.
 */
export function DocumentList({
  documents = [],
  totalChunks = 0,
  isLoading = false,
  error = null,
  onRefresh,
  onDelete,
  onReplace,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingDoc, setDeletingDoc] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [replacingDoc, setReplacingDoc] = useState(null);
  const [isReplacing, setIsReplacing] = useState(false);
  const [notification, setNotification] = useState(null);

  // Filter documents by search query
  const filteredDocuments = useMemo(() => {
    if (!searchQuery.trim()) return documents;
    const q = searchQuery.toLowerCase().trim();
    return documents.filter((doc) => doc.source.toLowerCase().includes(q));
  }, [documents, searchQuery]);

  async function handleConfirmDelete(source) {
    setIsDeleting(true);
    try {
      await onDelete(source);
      setNotification({
        type: 'success',
        message: `Document '${source}' deleted successfully.`,
      });
      setDeletingDoc(null);
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || `Failed to delete '${source}'.`,
      });
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleConfirmReplace(file) {
    if (!replacingDoc) return;
    setIsReplacing(true);
    try {
      await onReplace(replacingDoc.source, file);
      setNotification({
        type: 'success',
        message: `Document '${replacingDoc.source}' replaced with '${file.name}'.`,
      });
      setReplacingDoc(null);
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Failed to replace document.',
      });
      throw err;
    } finally {
      setIsReplacing(false);
    }
  }

  return (
    <div className="document-list-card" data-testid="document-list">
      {/* List Header */}
      <div className="document-list-header">
        <div className="list-title-group">
          <h2 className="list-title">Indexed Knowledge</h2>
          <div className="list-meta-stats">
            <span className="stat-pill">
              <strong>{documents.length}</strong>{' '}
              {documents.length === 1 ? 'document' : 'documents'}
            </span>
            <span className="stat-separator">•</span>
            <span className="stat-pill">
              <strong>{totalChunks}</strong> total chunks
            </span>
          </div>
        </div>

        <div className="list-controls">
          {/* Search Input */}
          <div className="search-input-wrapper">
            <svg
              className="search-icon"
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              className="search-input"
              placeholder="Filter documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Filter documents"
              data-testid="filter-docs-input"
            />
            {searchQuery && (
              <button
                type="button"
                className="btn-clear-search"
                onClick={() => setSearchQuery('')}
                aria-label="Clear filter"
              >
                ×
              </button>
            )}
          </div>

          {/* Refresh Button */}
          <button
            type="button"
            className="btn-icon-refresh"
            onClick={onRefresh}
            disabled={isLoading}
            title="Refresh documents list"
            aria-label="Refresh documents"
            data-testid="refresh-docs-btn"
          >
            <svg
              className={isLoading ? 'spinning' : ''}
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="23 4 23 10 17 10" />
              <polyline points="1 20 1 14 7 14" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
          </button>
        </div>
      </div>

      {/* Action Notification Banner */}
      {notification && (
        <div
          className={`alert-banner ${
            notification.type === 'success' ? 'alert-success' : 'alert-error'
          }`}
          role="alert"
        >
          <span>{notification.message}</span>
          <button
            type="button"
            className="alert-dismiss"
            onClick={() => setNotification(null)}
          >
            ×
          </button>
        </div>
      )}

      {/* Fetch Error Banner */}
      {error && !isLoading && (
        <div className="alert-banner alert-error" role="alert">
          <span>{error}</span>
          <button
            type="button"
            className="btn-secondary btn-sm"
            onClick={onRefresh}
          >
            Retry
          </button>
        </div>
      )}

      {/* Table / Content Area */}
      <div className="table-container">
        {isLoading ? (
          <div className="skeleton-table" data-testid="loading-skeleton">
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton-row">
                <div className="skeleton-col col-name-skel" />
                <div className="skeleton-col col-type-skel" />
                <div className="skeleton-col col-chunks-skel" />
                <div className="skeleton-col col-date-skel" />
                <div className="skeleton-col col-actions-skel" />
              </div>
            ))}
          </div>
        ) : filteredDocuments.length === 0 ? (
          <EmptyDocumentState
            isFiltered={documents.length > 0 && searchQuery.trim().length > 0}
            onResetFilter={() => setSearchQuery('')}
          />
        ) : (
          <table className="documents-table" data-testid="documents-table">
            <thead>
              <tr>
                <th className="th-name">Document</th>
                <th className="th-type">Type</th>
                <th className="th-chunks">Chunks</th>
                <th className="th-date">Indexed</th>
                <th className="th-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocuments.map((doc) => (
                <DocumentRow
                  key={doc.source}
                  document={doc}
                  onDeleteClick={(d) => setDeletingDoc(d)}
                  onReplaceClick={(d) => setReplacingDoc(d)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modals */}
      <DeleteConfirmModal
        isOpen={Boolean(deletingDoc)}
        document={deletingDoc}
        onConfirm={handleConfirmDelete}
        onClose={() => setDeletingDoc(null)}
        isDeleting={isDeleting}
      />

      <ReplaceDocumentModal
        isOpen={Boolean(replacingDoc)}
        document={replacingDoc}
        onConfirm={handleConfirmReplace}
        onClose={() => setReplacingDoc(null)}
        isReplacing={isReplacing}
      />
    </div>
  );
}
