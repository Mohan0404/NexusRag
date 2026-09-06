import React from 'react';
import { getFileTypeBadge, formatDate } from '../utils/helpers';

/**
 * Single document row inside the DocumentList table.
 * Clean, non-overlapping columns with accessible tooltips and action buttons.
 */
export function DocumentRow({ document, onDeleteClick, onReplaceClick }) {
  const badge = getFileTypeBadge(document.source || document.file_type);

  return (
    <tr className="document-row" data-testid={`document-row-${document.source}`}>
      <td className="col-name">
        <div className="doc-name-cell">
          <svg
            className="doc-file-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          <span className="doc-filename" title={document.source}>
            {document.source}
          </span>
        </div>
      </td>

      <td className="col-type">
        <span className={`file-badge ${badge.colorClass}`}>
          {badge.label}
        </span>
      </td>

      <td className="col-chunks">
        <span className="chunk-count-badge">
          {document.chunk_count} {document.chunk_count === 1 ? 'chunk' : 'chunks'}
        </span>
      </td>

      <td className="col-date text-muted">
        <span title={document.indexed_at || 'Not recorded'}>
          {formatDate(document.indexed_at)}
        </span>
      </td>

      <td className="col-actions">
        <div className="action-btn-group">
          <button
            type="button"
            className="action-btn btn-replace"
            title={`Replace and re-index ${document.source}`}
            onClick={() => onReplaceClick(document)}
            data-testid={`replace-btn-${document.source}`}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            <span>Replace</span>
          </button>

          <button
            type="button"
            className="action-btn btn-delete"
            title={`Delete ${document.source}`}
            onClick={() => onDeleteClick(document)}
            data-testid={`delete-btn-${document.source}`}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
            <span>Delete</span>
          </button>
        </div>
      </td>
    </tr>
  );
}

export default DocumentRow;
