/**
 * Centralized API client service for NexusRAG.
 * Consumes the FastAPI backend endpoints using native window.fetch().
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Custom ApiError encapsulating HTTP status, backend detail, and a user-friendly message.
 */
export class ApiError extends Error {
  constructor(message, status = 0, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Maps HTTP status codes and backend error details into clear user-friendly messages.
 *
 * @param {number} status
 * @param {any} detail
 * @param {'chat' | 'upload' | 'health' | 'documents' | 'delete' | 'replace'} context
 * @returns {string}
 */
export function normalizeErrorMessage(status, detail, context = 'chat') {
  if (typeof detail === 'string' && detail.trim()) {
    // If backend returned a clear human-readable string, use it directly for 400/404/413
    if (status === 400 || status === 404 || status === 413) {
      return detail;
    }
    if (status === 502) {
      return 'The AI service is temporarily unavailable. Please try again shortly.';
    }
  }

  // Check validation error arrays from Pydantic (status 422)
  if (status === 422) {
    if (context === 'chat') {
      return 'Question must be between 1 and 2,000 characters and cannot be blank.';
    }
    return 'Document could not be processed or contains no readable text.';
  }

  switch (status) {
    case 400:
      return 'Unsupported file type. Please upload PDF, TXT, or Markdown.';
    case 404:
      return 'Document not found in the knowledge base.';
    case 413:
      return 'File is larger than the 10 MB limit.';
    case 500:
      if (context === 'upload') return 'Document processing failed. Please try again.';
      if (context === 'delete') return 'Failed to delete document from the knowledge base.';
      if (context === 'replace') return 'Failed to replace document. Please try again.';
      if (context === 'documents') return 'Failed to load documents. Please try again.';
      return 'An internal server error occurred while processing your question.';
    case 502:
      return 'The AI service is temporarily unavailable. Please try again.';
    default:
      return `Request failed with status ${status}. Please try again.`;
  }
}

/**
 * Parses response JSON safely, falling back to null if response is not JSON.
 */
async function parseJsonSafely(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

/**
 * Checks backend health status.
 *
 * @returns {Promise<{ status: string }>}
 */
export async function checkHealth() {
  try {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) {
      throw new ApiError(`Health check failed (${res.status})`, res.status);
    }
    const data = await parseJsonSafely(res);
    return data || { status: 'healthy' };
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Unable to connect to the NexusRAG backend.', 0);
  }
}

/**
 * Sends a question to the RAG pipeline.
 *
 * @param {string} question - User question string.
 * @returns {Promise<{
 *   answer: string,
 *   sources: Array<{ source: string, file_type: string, page: number }>,
 *   query: string,
 *   model: string,
 *   context_chunks_used: number
 * }>}
 */
export async function sendChatMessage(question) {
  let response;
  try {
    response = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });
  } catch (netErr) {
    throw new ApiError('Unable to connect to the NexusRAG backend.', 0, netErr.message);
  }

  const data = await parseJsonSafely(response);

  if (!response.ok) {
    const detail = data?.detail;
    const userMessage = normalizeErrorMessage(response.status, detail, 'chat');
    throw new ApiError(userMessage, response.status, detail);
  }

  return data;
}

/**
 * Uploads a document file (.pdf, .txt, .md) to the ingestion pipeline.
 *
 * @param {File} file - Binary file object.
 * @returns {Promise<{
 *   filename: string,
 *   file_type: string,
 *   file_size_bytes: number,
 *   chunks_created: number,
 *   status: string,
 *   message: string
 * }>}
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  let response;
  try {
    response = await fetch(`${BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
  } catch (netErr) {
    throw new ApiError('Unable to connect to the NexusRAG backend.', 0, netErr.message);
  }

  const data = await parseJsonSafely(response);

  if (!response.ok) {
    const detail = data?.detail;
    const userMessage = normalizeErrorMessage(response.status, detail, 'upload');
    throw new ApiError(userMessage, response.status, detail);
  }

  return data;
}

/**
 * Lists all documents currently indexed in ChromaDB.
 *
 * @returns {Promise<{
 *   documents: Array<{
 *     source: string,
 *     file_type: string,
 *     chunk_count: number,
 *     indexed_at: string | null
 *   }>,
 *   total_chunks: number
 * }>}
 */
export async function listDocuments() {
  let response;
  try {
    response = await fetch(`${BASE_URL}/documents`);
  } catch (netErr) {
    throw new ApiError('Unable to connect to the NexusRAG backend.', 0, netErr.message);
  }

  const data = await parseJsonSafely(response);

  if (!response.ok) {
    const detail = data?.detail;
    const userMessage = normalizeErrorMessage(response.status, detail, 'documents');
    throw new ApiError(userMessage, response.status, detail);
  }

  return data;
}

/**
 * Deletes a document and its indexed chunks from ChromaDB and clears query cache.
 *
 * @param {string} source - Document source identifier (filename).
 * @returns {Promise<{
 *   source: string,
 *   chunks_deleted: number,
 *   status: string
 * }>}
 */
export async function deleteDocument(source) {
  let response;
  try {
    response = await fetch(`${BASE_URL}/documents/${encodeURIComponent(source)}`, {
      method: 'DELETE',
    });
  } catch (netErr) {
    throw new ApiError('Unable to connect to the NexusRAG backend.', 0, netErr.message);
  }

  const data = await parseJsonSafely(response);

  if (!response.ok) {
    const detail = data?.detail;
    const userMessage = normalizeErrorMessage(response.status, detail, 'delete');
    throw new ApiError(userMessage, response.status, detail);
  }

  return data;
}

/**
 * Replaces an existing indexed document with a new uploaded file.
 *
 * @param {string} source - Old document source identifier to replace.
 * @param {File} file - New replacement binary file object.
 * @returns {Promise<{
 *   filename: string,
 *   file_type: string,
 *   file_size_bytes: number,
 *   chunks_created: number,
 *   status: string,
 *   message: string
 * }>}
 */
export async function replaceDocument(source, file) {
  const formData = new FormData();
  formData.append('file', file);

  let response;
  try {
    response = await fetch(`${BASE_URL}/documents/${encodeURIComponent(source)}`, {
      method: 'PUT',
      body: formData,
    });
  } catch (netErr) {
    throw new ApiError('Unable to connect to the NexusRAG backend.', 0, netErr.message);
  }

  const data = await parseJsonSafely(response);

  if (!response.ok) {
    const detail = data?.detail;
    const userMessage = normalizeErrorMessage(response.status, detail, 'replace');
    throw new ApiError(userMessage, response.status, detail);
  }

  return data;
}
