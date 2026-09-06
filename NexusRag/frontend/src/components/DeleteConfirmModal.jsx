import React, { useEffect } from 'react';

/**
 * Confirmation dialog for destructive document deletion.
 */
export function DeleteConfirmModal({
  isOpen,
  document,
  onConfirm,
  onClose,
  isDeleting,
}) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && !isDeleting) {
        onClose();
      }
    }
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isDeleting, onClose]);

  if (!isOpen || !document) return null;

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isDeleting) {
          onClose();
        }
      }}
    >
      <div className="modal-card delete-modal-card">
        <div className="modal-header">
          <div className="modal-icon-badge danger-badge">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              <line x1="10" y1="11" x2="10" y2="17" />
              <line x1="14" y1="11" x2="14" y2="17" />
            </svg>
          </div>
          <div>
            <h3 id="delete-modal-title" className="modal-title">
              Delete Document
            </h3>
            <p className="modal-subtitle">This action cannot be undone.</p>
          </div>
        </div>

        <div className="modal-body">
          <p className="modal-message">
            Are you sure you want to delete{' '}
            <strong className="text-highlight">{document.source}</strong>?
          </p>
          <div className="delete-impact-info">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>
              All <strong>{document.chunk_count || 0} chunk(s)</strong> and
              associated vector embeddings will be permanently removed, and the
              query cache will be invalidated.
            </span>
          </div>
        </div>

        <div className="modal-footer">
          <button
            type="button"
            className="btn-secondary"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn-danger"
            onClick={() => onConfirm(document.source)}
            disabled={isDeleting}
            data-testid="confirm-delete-btn"
          >
            {isDeleting ? 'Deleting...' : 'Delete Document'}
          </button>
        </div>
      </div>
    </div>
  );
}
