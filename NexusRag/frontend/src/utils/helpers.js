/**
 * Helper utility functions for NexusRAG frontend.
 */

/**
 * Formats a byte number into a human-readable string (e.g. "1.4 MB").
 *
 * @param {number} bytes - Total number of bytes.
 * @param {number} decimals - Number of decimal places.
 * @returns {string} Human-readable byte representation.
 */
export function formatBytes(bytes, decimals = 1) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

/**
 * Strips leading directories or path traversal segments to display only the basename.
 *
 * @param {string} filepath - Raw path or filename from server.
 * @returns {string} Clean basename.
 */
export function sanitizeFilename(filepath) {
  if (!filepath) return 'unknown';
  // Handles both Unix and Windows separators
  return filepath.split(/[/\\]/).pop() || filepath;
}

/**
 * Returns formatting metadata for supported file extensions.
 *
 * @param {string} filename - Filename or extension.
 * @returns {{ label: string, colorClass: string }}
 */
export function getFileTypeBadge(filename) {
  const ext = (filename || '').split('.').pop().toLowerCase();
  switch (ext) {
    case 'pdf':
      return { label: 'PDF', colorClass: 'badge-pdf' };
    case 'txt':
      return { label: 'TXT', colorClass: 'badge-txt' };
    case 'md':
    case 'markdown':
      return { label: 'MD', colorClass: 'badge-md' };
    default:
      return { label: ext.toUpperCase() || 'FILE', colorClass: 'badge-default' };
  }
}

/**
 * Formats timestamp for chat messages.
 *
 * @param {Date|string} date
 * @returns {string} Formatted time (e.g. "10:45 AM")
 */
export function formatTime(date) {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Formats an ISO-8601 timestamp for document tables.
 *
 * @param {string} isoString
 * @returns {string} Formatted date string or '—'
 */
export function formatDate(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '—';
  }
}
