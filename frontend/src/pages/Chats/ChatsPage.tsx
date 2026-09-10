import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { useSearchParams } from "react-router-dom";

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
    conversation: Conversation | null,
  ) => void;
}

export default function ChatsPage({
  onConversationSelected,
}: ChatsPageProps) {
  // =========================================================
  // URL PARAMETERS
  // =========================================================

  const [searchParams] = useSearchParams();

  const customerIdParam =
    searchParams.get("customerId");

  const requestedCustomerId =
    customerIdParam !== null
      ? Number(customerIdParam)
      : null;

  // =========================================================
  // STATE
  // =========================================================

  const [conversations, setConversations] =
    useState<Conversation[]>([]);

  const [
    selectedConversationId,
    setSelectedConversationId,
  ] = useState<number | null>(null);

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

  // =========================================================
  // SELECTED CONVERSATION REF
  // =========================================================

  const selectedConversationIdRef =
    useRef<number | null>(null);

  useEffect(() => {
    selectedConversationIdRef.current =
      selectedConversationId;
  }, [selectedConversationId]);

  // =========================================================
  // CURRENT CONVERSATION
  // =========================================================

  const selectedConversation =
    conversations.find(
      (conversation) =>
        conversation.id ===
        selectedConversationId,
    ) ?? null;

  // =========================================================
  // LOAD CONVERSATIONS
  // =========================================================

  const loadConversations =
    useCallback(async () => {
      try {
        setLoading(true);

        const data =
          await getConversations();

        setConversations(data);

        /*
         * Priority:
         *
         * 1. Customer from URL
         * 2. Currently selected conversation
         * 3. First conversation
         * 4. Nothing
         */

        let nextSelectedConversationId:
          | number
          | null = null;

        // -----------------------------------------------------
        // 1. Customer specified in URL
        // -----------------------------------------------------

        if (
          requestedCustomerId !== null &&
          !Number.isNaN(requestedCustomerId)
        ) {
          const customerConversation =
            data.find(
              (conversation) =>
                conversation.customer.id ===
                requestedCustomerId,
            );

          if (customerConversation) {
            nextSelectedConversationId =
              customerConversation.id;
          }
        }

        // -----------------------------------------------------
        // 2. Keep current conversation
        // -----------------------------------------------------

        if (
          nextSelectedConversationId ===
          null
        ) {
          const currentConversation =
            data.find(
              (conversation) =>
                conversation.id ===
                selectedConversationIdRef.current,
            );

          if (currentConversation) {
            nextSelectedConversationId =
              currentConversation.id;
          }
        }

        // -----------------------------------------------------
        // 3. Select first conversation
        // -----------------------------------------------------

        if (
          nextSelectedConversationId ===
            null &&
          data.length > 0
        ) {
          nextSelectedConversationId =
            data[0].id;
        }

        // -----------------------------------------------------
        // 4. Set selection
        // -----------------------------------------------------

        setSelectedConversationId(
          nextSelectedConversationId,
        );
      } catch (error) {
        console.error(
          "Failed to load conversations:",
          error,
        );
      } finally {
        setLoading(false);
      }
    }, [requestedCustomerId]);

  // =========================================================
  // LOAD MESSAGES
  // =========================================================

  const loadMessages = useCallback(
    async (conversationId: number) => {
      setLoadingMessages(true);

      try {
        const data =
          await getConversationMessages(
            conversationId,
          );

        const sortedMessages =
          [...data].sort(
            (a, b) =>
              new Date(
                a.created_at,
              ).getTime() -
              new Date(
                b.created_at,
              ).getTime(),
          );

        setMessages(sortedMessages);
      } catch (error) {
        console.error(
          "Failed to load messages:",
          error,
        );

        setMessages([]);
      } finally {
        setLoadingMessages(false);
      }
    },
    [],
  );

  // =========================================================
  // MARK CONVERSATION READ
  // =========================================================

  const markSelectedConversationRead =
    useCallback(
      async (conversationId: number) => {
        try {
          const result =
            await markConversationRead(
              conversationId,
            );

          setConversations(
            (current) =>
              current.map(
                (conversation) =>
                  conversation.id ===
                  conversationId
                    ? {
                        ...conversation,
                        unread_count:
                          result.unread_count,
                      }
                    : conversation,
              ),
          );
        } catch (error) {
          console.error(
            "Failed to mark conversation as read:",
            error,
          );
        }
      },
      [],
    );

  // =========================================================
  // REALTIME WEBSOCKET EVENTS
  // =========================================================

  const handleDashboardEvent =
    useCallback(
      (event: DashboardEvent) => {
        const selectedId =
          selectedConversationIdRef.current;

        // =====================================================
        // MESSAGE CREATED
        // =====================================================

        if (
          event.type ===
            "message.created" &&
          event.message
        ) {
          const newMessage =
            event.message as Message;

          console.log(
            "[WS] message.created",
            newMessage,
          );

          // ---------------------------------------------------
          // Add message to currently open conversation
          // ---------------------------------------------------

          if (
            newMessage.conversation_id ===
            selectedId
          ) {
            setMessages((current) => {
              const exists =
                current.some(
                  (message) =>
                    message.id ===
                    newMessage.id,
                );

              if (exists) {
                return current;
              }

              return [
                ...current,
                newMessage,
              ];
            });

            /*
             * If the inbound message belongs to the
             * currently open conversation, mark it read.
             */

            if (
              newMessage.direction ===
              "inbound"
            ) {
              void markSelectedConversationRead(
                newMessage.conversation_id,
              );
            }
          }

          // ---------------------------------------------------
          // Update conversation preview
          // ---------------------------------------------------

          setConversations(
            (current) =>
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
                      read_at:
                        newMessage.read_at,
                      created_at:
                        newMessage.created_at,
                    },

                    last_message_at:
                      newMessage.created_at,

                    updated_at:
                      new Date().toISOString(),

                    unread_count:
                      isCurrentConversation
                        ? 0
                        : conversation.unread_count +
                          (isInbound
                            ? 1
                            : 0),
                  };
                },
              ),
          );

          return;
        }

        // =====================================================
        // MESSAGE UPDATED
        // =====================================================

        if (
          event.type ===
            "message.updated" &&
          event.message
        ) {
          const updatedMessage =
            event.message as Message;

          console.log(
            "[WS] message.updated",
            updatedMessage,
          );

          // ---------------------------------------------------
          // Update message inside open chat
          // ---------------------------------------------------

          if (
            updatedMessage.conversation_id ===
            selectedId
          ) {
            setMessages((current) => {
              const exists =
                current.some(
                  (message) =>
                    message.id ===
                    updatedMessage.id,
                );

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
                    : message,
              );
            });
          }

          // ---------------------------------------------------
          // Update last message status
          // ---------------------------------------------------

          setConversations(
            (current) =>
              current.map(
                (conversation) => {
                  if (
                    conversation.id !==
                    updatedMessage.conversation_id
                  ) {
                    return conversation;
                  }

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

                      read_at:
                        updatedMessage.read_at,
                    },

                    updated_at:
                      new Date().toISOString(),
                  };
                },
              ),
          );

          return;
        }

        // =====================================================
        // CONVERSATION UPDATED
        // =====================================================

        if (
          event.type ===
          "conversation.updated"
        ) {
          const conversationId =
            event.conversation_id;

          console.log(
            "[WS] conversation.updated",
            event,
          );

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

          setConversations(
            (current) =>
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
                },
              ),
          );
        }
      },
      [markSelectedConversationRead],
    );

  // =========================================================
  // SINGLE PERSISTENT WEBSOCKET
  // =========================================================

  useDashboardWebSocket({
    onEvent:
      handleDashboardEvent,
  });

  // =========================================================
  // INITIAL LOAD
  // =========================================================

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  // =========================================================
  // CONVERSATION SELECTION
  // =========================================================

  useEffect(() => {
    if (
      selectedConversationId ===
      null
    ) {
      setMessages([]);

      onConversationSelected?.(
        null,
      );

      return;
    }

    void loadMessages(
      selectedConversationId,
    );

    void markSelectedConversationRead(
      selectedConversationId,
    );
  }, [
    selectedConversationId,
    loadMessages,
    markSelectedConversationRead,
    onConversationSelected,
  ]);

  // =========================================================
  // RIGHT CUSTOMER PANEL
  // =========================================================

  useEffect(() => {
    onConversationSelected?.(
      selectedConversation,
    );
  }, [
    selectedConversation,
    onConversationSelected,
  ]);

  // =========================================================
  // SELECT CONVERSATION
  // =========================================================

  const handleSelectConversation = (
    conversation: Conversation,
  ) => {
    setSelectedConversationId(
      conversation.id,
    );
  };

  // =========================================================
  // SEND MESSAGE
  // =========================================================

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
       * Backend creates the message in QUEUED state.
       */

      const queuedMessage =
        await sendConversationMessage(
          selectedConversationId,
          text,
        );

      console.log(
        "[CHAT] Message queued:",
        queuedMessage,
      );

      /*
       * Immediately display the queued message.
       *
       * WebSocket duplicate is prevented by ID.
       */

      setMessages((current) => {
        const exists =
          current.some(
            (message) =>
              message.id ===
              queuedMessage.id,
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
       * No REST refresh here.
       *
       * WebSocket handles:
       *
       * message.created
       * message.updated
       * conversation.updated
       */
    } catch (error) {
      console.error(
        "Failed to send message:",
        error,
      );

      alert(
        "Failed to queue WhatsApp message.",
      );
    } finally {
      setSending(false);
    }
  };

  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <div className="chat-page-loading">
        Loading conversations...
      </div>
    );
  }

  // =========================================================
  // RENDER
  // =========================================================

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