import React, { useState, useRef, useEffect } from 'react';
import { formatBytes } from '../utils/helpers';

const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md', '.markdown'];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

/**
 * Modal dialog for replacing and re-indexing an existing document.
 */
export function ReplaceDocumentModal({
  isOpen,
  document,
  onConfirm,
  onClose,
  isReplacing,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!isOpen) {
      setSelectedFile(null);
      setValidationError(null);
      setIsDragOver(false);
    }
  }, [isOpen]);

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && !isReplacing) {
        onClose();
      }
    }
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isReplacing, onClose]);

  if (!isOpen || !document) return null;

  function validateAndSetFile(file) {
    setValidationError(null);
    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setValidationError('Unsupported format. Only PDF, TXT, and Markdown are supported.');
      setSelectedFile(null);
      return;
    }

    if (file.size === 0) {
      setValidationError('Selected file is empty (0 bytes).');
      setSelectedFile(null);
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setValidationError('File size exceeds the 10 MB limit.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    validateAndSetFile(file);
  }

  function handleDragOver(e) {
    e.preventDefault();
    setIsDragOver(true);
  }

  function handleDragLeave() {
    setIsDragOver(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    validateAndSetFile(file);
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    if (!selectedFile || isReplacing) return;
    try {
      await onConfirm(selectedFile);
      onClose();
    } catch (err) {
      setValidationError(err.message || 'Replacement failed. Please try again.');
    }
  }

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="replace-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isReplacing) {
          onClose();
        }
      }}
    >
      <div className="modal-card replace-modal-card">
        <div className="modal-header">
          <div className="modal-icon-badge primary-badge">
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
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
          </div>
          <div>
            <h3 id="replace-modal-title" className="modal-title">
              Replace & Re-index
            </h3>
            <p className="modal-subtitle">
              Replacing target: <strong className="text-highlight">{document.source}</strong>
            </p>
          </div>
        </div>

        <form onSubmit={handleFormSubmit}>
          <div className="modal-body">
            <p className="replace-desc">
              Select a new file. Existing chunks for{' '}
              <strong>{document.source}</strong> will be removed and replaced with
              new vector embeddings.
            </p>

            <div
              className={`replace-dropzone ${isDragOver ? 'drag-active' : ''} ${
                selectedFile ? 'has-file' : ''
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => !isReplacing && fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.md,.markdown"
                style={{ display: 'none' }}
                onChange={handleFileChange}
                disabled={isReplacing}
                data-testid="replace-file-input"
              />

              {!selectedFile ? (
                <div className="dropzone-prompt">
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <span>Click to choose file or drag & drop</span>
                  <small className="text-muted">PDF, TXT, or MD (up to 10 MB)</small>
                </div>
              ) : (
                <div className="selected-file-preview">
                  <div className="preview-file-icon">📄</div>
                  <div className="preview-file-info">
                    <span className="preview-filename">{selectedFile.name}</span>
                    <span className="preview-filesize text-muted">
                      {formatBytes(selectedFile.size)}
                    </span>
                  </div>
                  {!isReplacing && (
                    <button
                      type="button"
                      className="btn-icon-clear"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                      }}
                      title="Remove file"
                    >
                      ×
                    </button>
                  )}
                </div>
              )}
            </div>

            {validationError && (
              <div className="alert-banner alert-error" role="alert">
                <span>{validationError}</span>
              </div>
            )}

            {isReplacing && (
              <div className="replacing-progress">
                <div className="progress-info">
                  <span className="spinner-dot" />
                  <span>Uploading & re-indexing replacement...</span>
                </div>
                <div className="indeterminate-progress-bar">
                  <div className="indeterminate-fill" />
                </div>
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={isReplacing}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={!selectedFile || isReplacing}
              data-testid="confirm-replace-btn"
            >
              {isReplacing ? 'Processing...' : 'Replace & Re-index'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
