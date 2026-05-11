export type AttachmentType = "file" | "image" | "pdf";

export type AttachmentMetadata = {
  id: string;
  file_name: string;
  file_type: string;
  attachment_type?: AttachmentType;
  file_size: number;
  created_at: string;
};

export type ChatAttachment = AttachmentMetadata;

export type FileUploadResponse = {
  attachments: AttachmentMetadata[];
};
