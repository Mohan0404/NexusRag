import { useState, useEffect, useCallback } from 'react';
import { listDocuments, deleteDocument, replaceDocument } from '../services/api';

/**
 * Custom hook for managing document list and CRUD operations in NexusRAG.
 */
export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isMutating, setIsMutating] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listDocuments();
      setDocuments(data.documents || []);
      setTotalChunks(data.total_chunks || 0);
    } catch (err) {
      setError(err.message || 'Failed to load documents.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const deleteDoc = useCallback(
    async (source) => {
      setIsMutating(true);
      setError(null);
      try {
        const result = await deleteDocument(source);
        // Optimistically remove from state
        setDocuments((prev) => prev.filter((doc) => doc.source !== source));
        setTotalChunks((prev) => Math.max(0, prev - (result.chunks_deleted || 0)));
        return result;
      } catch (err) {
        setError(err.message || 'Failed to delete document.');
        throw err;
      } finally {
        setIsMutating(false);
      }
    },
    []
  );

  const replaceDoc = useCallback(
    async (source, file) => {
      setIsMutating(true);
      setError(null);
      try {
        const result = await replaceDocument(source, file);
        // Refetch full list to update chunk counts and timestamps cleanly
        await fetchDocuments();
        return result;
      } catch (err) {
        setError(err.message || 'Failed to replace document.');
        throw err;
      } finally {
        setIsMutating(false);
      }
    },
    [fetchDocuments]
  );

  return {
    documents,
    totalChunks,
    isLoading,
    error,
    isMutating,
    fetchDocuments,
    deleteDoc,
    replaceDoc,
    setError,
  };
}
