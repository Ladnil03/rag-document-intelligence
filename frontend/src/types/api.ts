// Centralised TypeScript types mirroring backend Pydantic schemas in
// backend/schemas.py. They describe the wire format the frontend expects
// from /auth, /documents, /conversations and related endpoints.

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export type ProcessingStatus = "UPLOADED" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface Document {
  id: number;
  name: string;
  stored_file_path: string | null;
  file_type: string | null;
  file_size: number | null;
  created_at: string;
  processing_status: ProcessingStatus;
}

export interface QuerySource {
  document_id: number;
  filename: string;
  chunk_index: number;
  similarity: number;
  page_number?: number | null;
}

export interface QueryResponse {
  answer: string;
  sources: QuerySource[];
  has_relevant_context: boolean;
}

export type MessageRole = "user" | "assistant";

export interface Message {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface ApiError {
  detail: string;
}
