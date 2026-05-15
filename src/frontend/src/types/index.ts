export type { AttachmentMetadata, AttachmentType, ChatAttachment, FileUploadResponse } from "./attachment";
export type { PdfUploadResponse, PdfProcessingStatus } from "./rag";
export type { SqlQueryResult } from "./sql";
import type { ChatAttachment } from "./attachment";

export type ChatRole = "user" | "assistant";

export type ChatApiMessage = {
	role: ChatRole;
	content: string;
};

export type ChatRequest = {
	message: string;
	thread_id: string;
	attachment_ids?: string[];
};

export type ChatUiMessage = ChatApiMessage & {
	id: string;
	attachment_ids?: string[];
	attachments?: ChatAttachment[];
};

export type AuthUser = {
	email: string;
};

export type LoginResponse = {
	access_token: string;
	token_type: string;
	user: AuthUser;
};

export type ChatHistoryMessage = {
	id: string;
	role: ChatRole;
	content: string;
	attachment_ids?: string[];
	created_at: string;
};

export type ChatThread = {
	id: string;
	name: string;
	created_at: string;
	updated_at: string;
};
