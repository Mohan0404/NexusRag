import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadDocument } from '../services/api';
import { formatBytes, sanitizeFilename, getFileTypeBadge } from '../utils/helpers';

const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md'];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

/**
 * Document uploader component implementing the approved state machine:
 * idle -> selected -> uploading (indeterminate) -> success / error.
 */
export function DocumentUploader({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle' | 'selected' | 'uploading' | 'success' | 'error'
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  /**
   * Validates selected file on client-side for UX feedback.
   */
  const validateFile = (selectedFile) => {
    if (!selectedFile) return 'No file selected.';

    const ext = `.${selectedFile.name.split('.').pop().toLowerCase()}`;
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file format '${ext}'. Allowed formats: PDF (.pdf), Text (.txt), Markdown (.md).`;
    }

    if (selectedFile.size === 0) {
      return 'The selected file is empty (0 bytes). Please select a valid document.';
    }

    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      return `File exceeds the maximum size limit of 10 MB (${formatBytes(selectedFile.size)}).`;
    }

    return null;
  };

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;

    const validationError = validateFile(selectedFile);
    if (validationError) {
      setFile(null);
      setErrorMessage(validationError);
      setUploadStatus('error');
      return;
    }

    setFile(selectedFile);
    setErrorMessage(null);
    setUploadStatus('selected');
  };

  const onFileInputChange = (e) => {
    const selected = e.target.files?.[0];
    handleFileSelect(selected);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const onDragLeave = () => {
    setIsDragActive(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    const droppedFile = e.dataTransfer.files?.[0];
    handleFileSelect(droppedFile);
  };

  /**
   * Triggers the upload using FormData and native fetch via api.js.
   */
  const handleUpload = async () => {
    if (!file || uploadStatus === 'uploading') return;

    setUploadStatus('uploading');
    setErrorMessage(null);

    try {
      const result = await uploadDocument(file);
      setUploadResult(result);
      setUploadStatus('success');
      if (typeof onUploadSuccess === 'function') {
        onUploadSuccess(result);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Document upload failed. Please try again.');
      setUploadStatus('error');
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadResult(null);
    setErrorMessage(null);
    setUploadStatus('idle');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="uploader-card" data-testid="document-uploader">
      {/* Hidden file input */}
      <input
        type="file"
        id="file-upload-input"
        ref={fileInputRef}
        onChange={onFileInputChange}
        accept=".pdf,.txt,.md"
        style={{ display: 'none' }}
        data-testid="file-upload-input"
        aria-label="Select a document file"
      />

      {/* Drop Zone (Shown in idle / error states) */}
      {(uploadStatus === 'idle' || (uploadStatus === 'error' && !file)) && (
        <div
          className={`drop-zone ${isDragActive ? 'drag-active' : ''}`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click();
          }}
          aria-label="Upload document drop zone. Click or drag a file here."
          data-testid="drop-zone"
        >
          <div className="drop-icon" aria-hidden="true">
            📂
          </div>
          <div className="drop-text">Click to browse or drag and drop your document</div>
          <div className="drop-subtext">Maximum file size: 10 MB</div>
          <div className="format-pills">
            <span className="format-pill">PDF (.pdf)</span>
            <span className="format-pill">Text (.txt)</span>
            <span className="format-pill">Markdown (.md)</span>
          </div>
        </div>
      )}

      {/* Selected State: Displays File Details */}
      {(uploadStatus === 'selected' || (uploadStatus === 'error' && file)) && (
        <div>
          <div className="file-selected-box">
            <div className="file-info">
              <span className={`source-badge ${getFileTypeBadge(file.name).colorClass}`}>
                {getFileTypeBadge(file.name).label}
              </span>
              <div>
                <div className="file-name">{sanitizeFilename(file.name)}</div>
                <div className="file-size">{formatBytes(file.size)}</div>
              </div>
            </div>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleReset}
              disabled={uploadStatus === 'uploading'}
              data-testid="cancel-file-btn"
            >
              Remove
            </button>
          </div>

          <div className="upload-actions">
            <button
              type="button"
              className="btn-primary"
              onClick={handleUpload}
              data-testid="upload-submit-btn"
            >
              Upload & Index
            </button>
          </div>
        </div>
      )}

      {/* Mandatory Correction #1: Indeterminate upload/indexing progress indicator */}
      {uploadStatus === 'uploading' && (
        <div className="uploading-box" data-testid="uploading-state">
          <div className="file-name" style={{ marginBottom: '0.4rem' }}>
            Uploading & indexing {sanitizeFilename(file.name)}...
          </div>
          <p className="drop-subtext">
            Extracting text, computing dense embeddings, and updating ChromaDB persistent vector store.
          </p>
          <div className="progress-bar-indeterminate" role="progressbar" aria-label="Uploading and indexing document" />
        </div>
      )}

      {/* Success State */}
      {uploadStatus === 'success' && uploadResult && (
        <div className="success-card" data-testid="upload-success-card">
          <div className="success-header">
            <span aria-hidden="true">✓</span> Indexed successfully
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{uploadResult.message}</p>
          <div className="success-stats">
            <div>
              <strong>Filename:</strong> {uploadResult.filename}
            </div>
            <div>
              <strong>Size:</strong> {formatBytes(uploadResult.file_size_bytes)}
            </div>
            <div>
              <strong>Chunks created:</strong> {uploadResult.chunks_created}
            </div>
          </div>
          <div className="upload-actions">
            <button
              type="button"
              className="btn-primary success-nav-btn"
              onClick={() => navigate('/chat')}
              data-testid="go-to-chat-btn"
            >
              Go to Chat 💬
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleReset}
              data-testid="upload-another-btn"
            >
              Upload Another
            </button>
          </div>
        </div>
      )}

      {/* Error Message Banner */}
      {uploadStatus === 'error' && errorMessage && (
        <div className="error-banner" style={{ marginTop: '1rem' }} role="alert" data-testid="upload-error-banner">
          <span>⚠️ {errorMessage}</span>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}

export default DocumentUploader;
