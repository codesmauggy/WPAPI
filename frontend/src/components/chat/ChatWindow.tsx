import { useEffect, useRef } from "react";
import type { KeyboardEvent } from "react";

import type { Conversation, Message } from "../../types/chat";
import MessageBubble from "./MessageBubble";

interface ChatWindowProps {
  conversation: Conversation | null;
  messages: Message[];
  messageText: string;
  sending: boolean;
  onMessageChange: (value: string) => void;
  onSend: () => void;
}

export default function ChatWindow({
  conversation,
  messages,
  messageText,
  sending,
  onMessageChange,
  onSend,
}: ChatWindowProps) {
  const messagesContainerRef = useRef<HTMLDivElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  /*
   * Scroll to the latest message.
   *
   * behavior:
   * - "auto" when opening/changing conversation
   * - "smooth" when a new message arrives
   */
  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    bottomRef.current?.scrollIntoView({
      behavior,
      block: "end",
    });
  };

  /*
   * When switching conversations, immediately show the
   * newest message.
   */
  useEffect(() => {
    if (!conversation) {
      return;
    }

    // Wait until messages have rendered.
    requestAnimationFrame(() => {
      scrollToBottom("auto");
    });
  }, [conversation?.id]);

  /*
   * When messages change, scroll to the newest message.
   *
   * We only auto-scroll if the user is already near the
   * bottom. This prevents the dashboard from jumping down
   * while the user is reading older messages.
   */
  useEffect(() => {
    if (!conversation || messages.length === 0) {
      return;
    }

    const container = messagesContainerRef.current;

    if (!container) {
      return;
    }

    const distanceFromBottom =
      container.scrollHeight -
      container.scrollTop -
      container.clientHeight;

    const isNearBottom = distanceFromBottom < 150;

    if (isNearBottom) {
      requestAnimationFrame(() => {
        scrollToBottom("smooth");
      });
    }
  }, [messages, conversation?.id]);

  if (!conversation) {
    return (
      <div className="chat-window empty">
        <div className="chat-empty-state">
          <div className="chat-empty-icon">💬</div>
          <h3>Select a conversation</h3>
          <p>
            Choose a conversation from the list to start messaging.
          </p>
        </div>
      </div>
    );
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      if (!sending && messageText.trim()) {
        onSend();
      }
    }
  };

  return (
    <div className="chat-window">
      {/* ---------------------------------------------------------
          Chat Header
      --------------------------------------------------------- */}
      <div className="chat-header">
        <div className="chat-header-avatar">
          {conversation.customer.name?.charAt(0)?.toUpperCase() || "?"}
        </div>

        <div className="chat-header-info">
          <div className="chat-header-name">
            {conversation.customer.name || "Unknown Customer"}
          </div>

          <div className="chat-header-phone">
            {conversation.customer.phone}
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------------
          Messages
      --------------------------------------------------------- */}
      <div
        ref={messagesContainerRef}
        className="chat-messages"
      >
        {messages.length === 0 ? (
          <div className="chat-no-messages">
            <div className="chat-no-messages-icon">👋</div>
            <p>No messages yet</p>
          </div>
        ) : (
          <>
            {messages.map((message: Message) => (
              <MessageBubble
                key={message.id}
                message={message}
              />
            ))}

            {/* Invisible element used as the scroll target */}
            <div
              ref={bottomRef}
              aria-hidden="true"
              style={{ height: 1 }}
            />
          </>
        )}
      </div>

      {/* ---------------------------------------------------------
          Composer
      --------------------------------------------------------- */}
      <div className="chat-composer">
        <textarea
          value={messageText}
          onChange={(event) => onMessageChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message"
          disabled={sending}
          rows={1}
        />

        <button
          type="button"
          onClick={onSend}
          disabled={sending || !messageText.trim()}
        >
          {sending ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}