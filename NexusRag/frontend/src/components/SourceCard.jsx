import React from 'react';
import { sanitizeFilename, getFileTypeBadge } from '../utils/helpers';

/**
 * Renders an individual grounded citation source pill/card.
 *
 * @param {{ source: { source: string, file_type: string, page?: number } }} props
 */
export function SourceCard({ source }) {
  if (!source) return null;

  const rawFilename = source.source || '';
  const cleanFilename = sanitizeFilename(rawFilename);
  const badgeInfo = getFileTypeBadge(cleanFilename);
  const hasPage = typeof source.page === 'number' && source.page > 0;

  return (
    <div className="source-card" data-testid="source-card">
      <span className={`source-badge ${badgeInfo.colorClass}`} aria-label={`File format ${badgeInfo.label}`}>
        {badgeInfo.label}
      </span>
      <span className="source-name" title={cleanFilename}>
        {cleanFilename}
      </span>
      {hasPage && (
        <span className="source-page" aria-label={`Page ${source.page}`}>
          Page {source.page}
        </span>
      )}
    </div>
  );
}

export default SourceCard;
