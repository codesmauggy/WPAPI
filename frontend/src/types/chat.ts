export type ConversationStatus = "open" | "closed";

export type MessageDirection = "inbound" | "outbound";

export type MessageStatus =
  | "received"
  | "queued"
  | "sending"
  | "sent"
  | "delivered"
  | "read"
  | "failed";

export interface ChatCustomer {
  id: number;
  name: string;
  phone: string;
  whatsapp_id: string;
}

export interface ChatPhoneNumber {
  id: number;
  display_name: string;
  phone_number: string;
  phone_number_id: string;
}

export interface ChatLastMessage {
  id: number;
  whatsapp_message_id: string | null;
  direction: MessageDirection;
  message_type: string;
  text: string;
  status: MessageStatus;
  read_at: string | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  customer: ChatCustomer;
  phone_number: ChatPhoneNumber;
  status: ConversationStatus;
  last_message_at: string | null;
  last_message: ChatLastMessage | null;
  unread_count: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  whatsapp_message_id: string | null;
  direction: MessageDirection;
  message_type: string;
  text: string;
  status: MessageStatus;
  read_at: string | null;
  created_at: string;
}

export interface ConversationsResponse {
  success: boolean;
  data: Conversation[];
  message: string;
  meta: {
    total: number;
  };
}

export interface MessagesResponse {
  success: boolean;
  data: Message[];
  message: string;
  meta: {
    conversation_id: number;
    total: number;
  };
}

export interface SendMessageResponse {
  success: boolean;
  data: {
    message: Message;
  };
  message: string;
  meta: Record<string, unknown>;
}

export interface MarkConversationReadResponse {
  success: boolean;
  data: {
    conversation_id: number;
    unread_count: number;
    updated_messages: number;
    read_at: string;
  };
  message: string;
  meta: Record<string, unknown>;
}
