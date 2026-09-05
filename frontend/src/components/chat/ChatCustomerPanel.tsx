import type { Conversation } from "../../types/chat";

interface ChatCustomerPanelProps {
  conversation: Conversation | null;
}

export default function ChatCustomerPanel({
  conversation,
}: ChatCustomerPanelProps) {
  if (!conversation) {
    return (
      <aside className="chat-customer-panel">
        <div className="chat-panel-empty">
          Select a conversation
        </div>
      </aside>
    );
  }

  return (
    <aside className="chat-customer-panel">
      <div className="chat-panel-profile">
        <div className="chat-panel-avatar">
          {conversation.customer.name
            ?.charAt(0)
            .toUpperCase() || "?"}
        </div>

        <h3>
          {conversation.customer.name ||
            "Unknown Customer"}
        </h3>

        <p>{conversation.customer.phone}</p>
      </div>

      <div className="chat-panel-section">
        <div className="chat-panel-label">
          WhatsApp ID
        </div>

        <div className="chat-panel-value">
          {conversation.customer.whatsapp_id}
        </div>
      </div>

      <div className="chat-panel-section">
        <div className="chat-panel-label">
          Conversation
        </div>

        <div className="chat-panel-value">
          #{conversation.id}
        </div>
      </div>

      <div className="chat-panel-section">
        <div className="chat-panel-label">
          Status
        </div>

        <div
          className={`chat-status ${conversation.status}`}
        >
          {conversation.status}
        </div>
      </div>

      <div className="chat-panel-section">
        <div className="chat-panel-label">
          WhatsApp Number
        </div>

        <div className="chat-panel-value">
          {conversation.phone_number.display_name}
        </div>
      </div>
    </aside>
  );
}