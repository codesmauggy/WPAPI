import type { Conversation } from "../../types/chat";

interface ConversationListProps {
  conversations: Conversation[];
  selectedConversationId: number | null;
  search: string;
  onSearchChange: (value: string) => void;
  onSelect: (conversation: Conversation) => void;
}

function formatTime(value: string | null) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ConversationList({
  conversations,
  selectedConversationId,
  search,
  onSearchChange,
  onSelect,
}: ConversationListProps) {
  const filtered = conversations.filter((conversation) => {
    const query = search.toLowerCase().trim();

    if (!query) {
      return true;
    }

    return (
      conversation.customer.name
        .toLowerCase()
        .includes(query) ||
      conversation.customer.phone.includes(query) ||
      conversation.last_message?.text
        ?.toLowerCase()
        .includes(query)
    );
  });

  return (
    <div className="chat-conversation-list">
      <div className="chat-list-search">
        <input
          type="text"
          placeholder="Search conversations"
          value={search}
          onChange={(event) =>
            onSearchChange(event.target.value)
          }
        />
      </div>

      <div className="chat-conversation-items">
        {filtered.length === 0 ? (
          <div className="chat-empty-list">
            No conversations found
          </div>
        ) : (
          filtered.map((conversation) => {
            const selected =
              conversation.id ===
              selectedConversationId;

            return (
              <button
                key={conversation.id}
                type="button"
                className={`chat-conversation-item ${
                  selected ? "selected" : ""
                }`}
                onClick={() =>
                  onSelect(conversation)
                }
              >
                <div className="chat-avatar">
                  {conversation.customer.name
                    ?.charAt(0)
                    .toUpperCase() || "?"}
                </div>

                <div className="chat-conversation-content">
                  <div className="chat-conversation-top">
                    <span className="chat-customer-name">
                      {conversation.customer.name ||
                        conversation.customer.phone}
                    </span>

                    <span className="chat-message-time">
                      {formatTime(
                        conversation.last_message_at
                      )}
                    </span>
                  </div>

                  <div className="chat-conversation-bottom">
                    <span className="chat-last-message">
                      {conversation.last_message
                        ?.text || "No messages"}
                    </span>

                    {conversation.unread_count >
                      0 && (
                      <span className="chat-unread-badge">
                        {conversation.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}