import { useState } from 'react';
import { uploadAttachments, uploadPdf } from '../lib/api';
import type { PdfProcessingStatus } from '../types';

interface UploadedAttachment {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  created_at: string;
}

export const useAttachments = () => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadedAttachments, setUploadedAttachments] = useState<UploadedAttachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [pdfStatus, setPdfStatus] = useState<PdfProcessingStatus>('idle');

  const addFiles = (files: File[]) => {
    const newFiles = Array.from(files);
    setSelectedFiles((prev) => [...prev, ...newFiles]);
    setUploadError(null);
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const removeAttachment = (id: string) => {
    setUploadedAttachments((prev) => prev.filter((att) => att.id !== id));
  };

  const uploadFiles = async (
    filesToUpload?: File[],
    options?: { mode?: 'normal' | 'upload' | 'upload_pdf_rag' | 'generate_image'; threadId?: string },
  ) => {
    const files = filesToUpload || selectedFiles;
    if (files.length === 0) return;
    const mode = options?.mode ?? 'upload';

    setIsUploading(true);
    setUploadError(null);
    if (mode === 'upload_pdf_rag') {
      setPdfStatus('uploading');
    }

    try {
      if (mode === 'upload_pdf_rag') {
        const file = files[0];
        if (!file) {
          throw new Error('Please select one PDF file.');
        }
        if (!options?.threadId) {
          throw new Error('A thread is required before uploading PDF for RAG.');
        }

        setPdfStatus('processing');
        const response = await uploadPdf(options.threadId, file);
        setUploadedAttachments((prev) => [...prev, response.attachment]);
        setPdfStatus('ready');
      } else {
        const formData = new FormData();
        files.forEach((file) => {
          formData.append('files', file);
        });

        const response = await uploadAttachments(formData);
        setUploadedAttachments((prev) => [...prev, ...response.attachments]);
      }

      if (!filesToUpload) {
        setSelectedFiles([]);
      }
    } catch (err) {
      if (mode === 'upload_pdf_rag') {
        setPdfStatus('error');
      }
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload files';
      setUploadError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const getAttachmentIds = () => uploadedAttachments.map((att) => att.id);

  const clearAttachments = () => {
    setSelectedFiles([]);
    setUploadedAttachments([]);
    setUploadError(null);
    setPdfStatus('idle');
  };

  return {
    selectedFiles,
    uploadedAttachments,
    isUploading,
    uploadError,
    pdfStatus,
    addFiles,
    removeFile,
    removeAttachment,
    uploadFiles,
    getAttachmentIds,
    clearAttachments,
  };
};
