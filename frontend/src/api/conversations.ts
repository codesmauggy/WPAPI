import apiClient from "./client";

import type {
  Conversation,
  ConversationsResponse,
  Message,
  MessagesResponse,
  SendMessageResponse,
} from "../types/chat";

export async function getConversations(): Promise<Conversation[]> {
  const response =
    await apiClient.get<ConversationsResponse>(
      "/conversations/"
    );

  return response.data.data;
}

export async function getConversationMessages(
  conversationId: number
): Promise<Message[]> {
  const response =
    await apiClient.get<MessagesResponse>(
      `/conversations/${conversationId}/messages/`
    );

  return response.data.data;
}

export async function sendConversationMessage(
  conversationId: number,
  message: string
): Promise<Message> {
  const response =
    await apiClient.post<SendMessageResponse>(
      `/conversations/${conversationId}/send/`,
      {
        message,
      }
    );

  return response.data.data.message;
}