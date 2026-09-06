import React from 'react';
import DocumentUploader from '../components/DocumentUploader';
import { DocumentList } from '../components/DocumentList';
import { useDocuments } from '../hooks/useDocuments';

/**
 * Documents page view for uploading and managing knowledge base files.
 * Provides complete Document Management CRUD operations alongside the upload panel.
 */
export function DocumentsPage() {
  const {
    documents,
    totalChunks,
    isLoading,
    error,
    fetchDocuments,
    deleteDoc,
    replaceDoc,
  } = useDocuments();

  return (
    <div className="documents-page" data-testid="documents-page">
      <div className="page-header">
        <h1 className="page-title">Knowledge Base Documents</h1>
        <p className="page-subtitle">
          Inspect, manage, and expand your enterprise knowledge base. Upload new documents,
          replace outdated files, or remove obsolete sources. All indexed documents are
          immediately retrievable in Chat.
        </p>
      </div>

      <div className="documents-grid">
        <section className="documents-main-panel" aria-label="Indexed Documents List">
          <DocumentList
            documents={documents}
            totalChunks={totalChunks}
            isLoading={isLoading}
            error={error}
            onRefresh={fetchDocuments}
            onDelete={deleteDoc}
            onReplace={replaceDoc}
          />
        </section>

        <aside className="documents-sidebar-panel" aria-label="Upload New Document">
          <div className="panel-sticky-wrapper">
            <div className="sidebar-card-header">
              <h3 className="sidebar-title">Add Document</h3>
              <p className="sidebar-subtitle">Index new information into ChromaDB</p>
            </div>
            <DocumentUploader onUploadSuccess={fetchDocuments} />
          </div>
        </aside>
      </div>
    </div>
  );
}

export default DocumentsPage;
