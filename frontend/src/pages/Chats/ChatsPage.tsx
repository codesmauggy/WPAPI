import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getConversations,
  getConversationMessages,
  markConversationRead,
  sendConversationMessage,
} from "../../api/conversations";

import type {
  Conversation,
  Message,
} from "../../types/chat";

import ConversationList from "../../components/chat/ConversationList";
import ChatWindow from "../../components/chat/ChatWindow";

import useDashboardWebSocket, {
  type DashboardEvent,
} from "../../hooks/useDashboardWebSocket";

interface ChatsPageProps {
  onConversationSelected?: (
    conversation: Conversation | null
  ) => void;
}

export default function ChatsPage({
  onConversationSelected,
}: ChatsPageProps) {
  /*
   * --------------------------------------------------
   * STATE
   * --------------------------------------------------
   */

  const [conversations, setConversations] =
    useState<Conversation[]>([]);

  const [selectedConversationId, setSelectedConversationId] =
    useState<number | null>(null);

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [search, setSearch] =
    useState("");

  const [messageText, setMessageText] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [loadingMessages, setLoadingMessages] =
    useState(false);

  const [sending, setSending] =
    useState(false);

  /*
   * --------------------------------------------------
   * SELECTED CONVERSATION REF
   * --------------------------------------------------
   *
   * The WebSocket should remain connected when the
   * operator changes conversations.
   *
   * This ref gives the realtime handler the latest
   * selected conversation without recreating the
   * WebSocket connection.
   */

  const selectedConversationIdRef =
    useRef<number | null>(null);

  useEffect(() => {
    selectedConversationIdRef.current =
      selectedConversationId;
  }, [selectedConversationId]);

  /*
   * --------------------------------------------------
   * CURRENT CONVERSATION
   * --------------------------------------------------
   */

  const selectedConversation =
    conversations.find(
      (conversation) =>
        conversation.id ===
        selectedConversationId
    ) ?? null;

  /*
   * --------------------------------------------------
   * LOAD CONVERSATIONS
   * --------------------------------------------------
   */

  const loadConversations =
    useCallback(async () => {
      try {
        const data =
          await getConversations();

        setConversations(data);

        /*
         * Keep current conversation selected if it
         * still exists.
         */
        setSelectedConversationId(
          (current) => {
            if (current !== null) {
              const exists = data.some(
                (conversation) =>
                  conversation.id === current
              );

              if (exists) {
                return current;
              }
            }

            /*
             * Automatically select first conversation
             * on initial load.
             */
            return data.length > 0
              ? data[0].id
              : null;
          }
        );
      } catch (error) {
        console.error(
          "Failed to load conversations:",
          error
        );
      } finally {
        setLoading(false);
      }
    }, []);

  /*
   * --------------------------------------------------
   * LOAD MESSAGES
   * --------------------------------------------------
   */

  const loadMessages = useCallback(
    async (conversationId: number) => {
      setLoadingMessages(true);

      try {
        const data =
          await getConversationMessages(
            conversationId
          );

        /*
         * Sort by creation time so the chat is always
         * displayed chronologically.
         */
        const sortedMessages =
          [...data].sort(
            (a, b) =>
              new Date(
                a.created_at
              ).getTime() -
              new Date(
                b.created_at
              ).getTime()
          );

        setMessages(sortedMessages);
      } catch (error) {
        console.error(
          "Failed to load messages:",
          error
        );

        setMessages([]);
      } finally {
        setLoadingMessages(false);
      }
    },
    []
  );

  /*
   * --------------------------------------------------
   * MARK CONVERSATION READ
   * --------------------------------------------------
   *
   * The database is the source of truth for dashboard
   * unread state. WebSocket distributes the resulting
   * conversation.updated event to connected clients.
   */

  const markSelectedConversationRead =
    useCallback(async (conversationId: number) => {
      try {
        const result =
          await markConversationRead(
            conversationId
          );

        setConversations((current) =>
          current.map((conversation) =>
            conversation.id === conversationId
              ? {
                  ...conversation,
                  unread_count: result.unread_count,
                }
              : conversation
          )
        );
      } catch (error) {
        console.error(
          "Failed to mark conversation as read:",
          error
        );
      }
    }, []);

  /*
   * --------------------------------------------------
   * REALTIME WEBSOCKET EVENTS
   * --------------------------------------------------
   *
   * IMPORTANT:
   *
   * There is NO manual:
   *
   *     new WebSocket(...)
   *
   * in this component.
   *
   * useDashboardWebSocket owns the connection.
   *
   * Supported events:
   *
   * message.created
   * message.updated
   * conversation.updated
   */

  const handleDashboardEvent =
    useCallback(
      (event: DashboardEvent) => {
        const selectedId =
          selectedConversationIdRef.current;

        /*
         * --------------------------------------------------
         * MESSAGE CREATED
         * --------------------------------------------------
         *
         * This handles BOTH:
         *
         * inbound messages
         * outbound queued messages
         */

        if (
          event.type ===
            "message.created" &&
          event.message
        ) {
          const newMessage =
            event.message as Message;

          console.log(
            "[WS] message.created",
            newMessage
          );

          /*
           * If this message belongs to the currently
           * open conversation, add it immediately.
           */
          if (
            newMessage.conversation_id ===
            selectedId
          ) {
            setMessages((current) => {
              /*
               * Prevent duplicate message when the API
               * response and WebSocket event arrive close
               * together.
               */
              const exists =
                current.some(
                  (message) =>
                    message.id ===
                    newMessage.id
                );

              if (exists) {
                return current;
              }

              return [
                ...current,
                newMessage,
              ];
            });

            // If the conversation is currently open, the
            // inbound message is immediately considered read
            // by the dashboard and persisted in the DB.
            if (newMessage.direction === "inbound") {
              void markSelectedConversationRead(
                newMessage.conversation_id
              );
            }
          }

          /*
           * Update conversation preview locally.
           *
           * No REST request required.
           */
          setConversations((current) =>
            current.map(
              (conversation) => {
                if (
                  conversation.id !==
                  newMessage.conversation_id
                ) {
                  return conversation;
                }

                const isCurrentConversation =
                  conversation.id ===
                  selectedId;

                const isInbound =
                  newMessage.direction ===
                  "inbound";

                return {
                  ...conversation,

                  last_message: {
                    id: newMessage.id,
                    whatsapp_message_id:
                      newMessage.whatsapp_message_id,
                    direction:
                      newMessage.direction,
                    message_type:
                      newMessage.message_type,
                    text:
                      newMessage.text,
                    status:
                      newMessage.status,
                    created_at:
                      newMessage.created_at,
                  },

                  last_message_at:
                    newMessage.created_at,

                  updated_at:
                    new Date().toISOString(),

                  /*
                   * Don't show an unread badge for a
                   * conversation the operator is already
                   * viewing.
                   */
                  unread_count:
                    isCurrentConversation
                      ? 0
                      : conversation.unread_count +
                        (isInbound
                          ? 1
                          : 0),
                };
              }
            )
          );

          return;
        }

        /*
         * --------------------------------------------------
         * MESSAGE UPDATED
         * --------------------------------------------------
         *
         * This is the important part for outbound
         * WhatsApp delivery lifecycle:
         *
         * queued
         *    ↓
         * sending
         *    ↓
         * sent
         *    ↓
         * delivered
         *    ↓
         * read
         *
         * Or:
         *
         * failed
         */

        if (
          event.type ===
            "message.updated" &&
          event.message
        ) {
          const updatedMessage =
            event.message as Message;

          console.log(
            "[WS] message.updated",
            updatedMessage
          );

          if (
            updatedMessage.conversation_id ===
            selectedId
          ) {
            setMessages((current) => {
              const exists =
                current.some(
                  (message) =>
                    message.id ===
                    updatedMessage.id
                );

              /*
               * If the original created event was missed,
               * don't lose the updated message.
               */
              if (!exists) {
                return [
                  ...current,
                  updatedMessage,
                ];
              }

              return current.map(
                (message) =>
                  message.id ===
                  updatedMessage.id
                    ? updatedMessage
                    : message
              );
            });
          }

          /*
           * Update last-message status in conversation list.
           */
          setConversations((current) =>
            current.map(
              (conversation) => {
                if (
                  conversation.id !==
                  updatedMessage.conversation_id
                ) {
                  return conversation;
                }

                /*
                 * Only replace the preview if this
                 * conversation's last message is the
                 * message being updated.
                 */
                if (
                  conversation.last_message
                    ?.id !==
                  updatedMessage.id
                ) {
                  return {
                    ...conversation,
                    updated_at:
                      new Date().toISOString(),
                  };
                }

                return {
                  ...conversation,

                  last_message: {
                    ...conversation.last_message,

                    whatsapp_message_id:
                      updatedMessage.whatsapp_message_id,

                    status:
                      updatedMessage.status,
                  },

                  updated_at:
                    new Date().toISOString(),
                };
              }
            )
          );

          return;
        }

        /*
         * --------------------------------------------------
         * CONVERSATION UPDATED
         * --------------------------------------------------
         */

        if (
          event.type ===
          "conversation.updated"
        ) {
          const conversationId =
            event.conversation_id;

          console.log(
            "[WS] conversation.updated",
            event
          );

          /*
           * DashboardEvent may contain additional
           * conversation fields depending on the
           * backend event.
           */
          const conversationEvent =
            event as DashboardEvent & {
              unread_count?: number;

              last_message_at?:
                | string
                | null;

              status?:
                | Conversation["status"];

              last_message?:
                | Conversation["last_message"];
            };

          setConversations((current) =>
            current.map(
              (conversation) => {
                if (
                  conversation.id !==
                  conversationId
                ) {
                  return conversation;
                }

                return {
                  ...conversation,

                  ...(conversationEvent.status !==
                  undefined
                    ? {
                        status:
                          conversationEvent.status,
                      }
                    : {}),

                  ...(conversationEvent.unread_count !==
                  undefined
                    ? {
                        unread_count:
                          conversationEvent.unread_count,
                      }
                    : {}),

                  ...(conversationEvent.last_message_at !==
                  undefined
                    ? {
                        last_message_at:
                          conversationEvent.last_message_at,
                      }
                    : {}),

                  ...(conversationEvent.last_message !==
                  undefined
                    ? {
                        last_message:
                          conversationEvent.last_message,
                      }
                    : {}),

                  updated_at:
                    new Date().toISOString(),
                };
              }
            )
          );
        }
      },
      [markSelectedConversationRead]
    );

  /*
   * --------------------------------------------------
   * SINGLE PERSISTENT WEBSOCKET
   * --------------------------------------------------
   */

  useDashboardWebSocket({
    onEvent:
      handleDashboardEvent,
  });

  /*
   * --------------------------------------------------
   * INITIAL LOAD
   * --------------------------------------------------
   */

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  /*
   * --------------------------------------------------
   * CONVERSATION SELECTION
   * --------------------------------------------------
   */

  useEffect(() => {
    if (
      selectedConversationId ===
      null
    ) {
      setMessages([]);

      onConversationSelected?.(
        null
      );

      return;
    }

    loadMessages(
      selectedConversationId
    );

    // Persist dashboard read state in the database.
    void markSelectedConversationRead(
      selectedConversationId
    );
  }, [
    selectedConversationId,
    loadMessages,
    markSelectedConversationRead,
    onConversationSelected,
  ]);

  /*
   * --------------------------------------------------
   * RIGHT CUSTOMER PANEL
   * --------------------------------------------------
   */

  useEffect(() => {
    onConversationSelected?.(
      selectedConversation
    );
  }, [
    selectedConversation,
    onConversationSelected,
  ]);

  /*
   * --------------------------------------------------
   * SELECT CONVERSATION
   * --------------------------------------------------
   */

  const handleSelectConversation = (
    conversation: Conversation
  ) => {
    setSelectedConversationId(
      conversation.id
    );
  };

  /*
   * --------------------------------------------------
   * SEND MESSAGE
   * --------------------------------------------------
   */

  const handleSend = async () => {
    const text =
      messageText.trim();

    if (
      !text ||
      selectedConversationId ===
        null ||
      sending
    ) {
      return;
    }

    setSending(true);

    try {
      /*
       * Backend returns the Message in QUEUED state.
       */
      const queuedMessage =
        await sendConversationMessage(
          selectedConversationId,
          text
        );

      console.log(
        "[CHAT] Message queued:",
        queuedMessage
      );

      /*
       * Add immediately so the operator doesn't have
       * to wait for the WebSocket event.
       *
       * WebSocket duplicate is prevented by ID check.
       */
      setMessages((current) => {
        const exists =
          current.some(
            (message) =>
              message.id ===
              queuedMessage.id
          );

        if (exists) {
          return current;
        }

        return [
          ...current,
          queuedMessage,
        ];
      });

      setMessageText("");

      /*
       * DO NOT call loadConversations() here.
       *
       * The WebSocket will update:
       *
       * message.created
       * message.updated
       * conversation.updated
       *
       * This removes the unnecessary REST request and
       * reduces UI lag.
       */
    } catch (error) {
      console.error(
        "Failed to send message:",
        error
      );

      alert(
        "Failed to queue WhatsApp message."
      );
    } finally {
      setSending(false);
    }
  };

  /*
   * --------------------------------------------------
   * LOADING
   * --------------------------------------------------
   */

  if (loading) {
    return (
      <div className="chat-page-loading">
        Loading conversations...
      </div>
    );
  }

  /*
   * --------------------------------------------------
   * RENDER
   * --------------------------------------------------
   */

  return (
    <div className="chat-page">
      <div className="chat-layout">

        <ConversationList
          conversations={
            conversations
          }
          selectedConversationId={
            selectedConversationId
          }
          search={search}
          onSearchChange={
            setSearch
          }
          onSelect={
            handleSelectConversation
          }
        />

        {loadingMessages ? (
          <div className="chat-window-loading">
            Loading messages...
          </div>
        ) : (
          <ChatWindow
            conversation={
              selectedConversation
            }
            messages={messages}
            messageText={
              messageText
            }
            sending={sending}
            onMessageChange={
              setMessageText
            }
            onSend={handleSend}
          />
        )}

      </div>
    </div>
  );
}