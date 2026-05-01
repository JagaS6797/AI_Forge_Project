export type ChatRole = "user" | "assistant";

export type ChatApiMessage = {
	role: ChatRole;
	content: string;
};

export type ChatRequest = {
	message: string;
	thread_id: string;
};

export type ChatUiMessage = ChatApiMessage & {
	id: string;
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
	created_at: string;
};

export type ChatThread = {
	id: string;
	name: string;
	created_at: string;
	updated_at: string;
};

	created_at: string;
};
