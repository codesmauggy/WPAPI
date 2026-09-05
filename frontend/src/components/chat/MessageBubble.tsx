import type { Message } from "../../types/chat";

interface MessageBubbleProps {
  message: Message;
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString(
    [],
    {
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}

function StatusIcon({
  status,
}: {
  status: Message["status"];
}) {
  switch (status) {
    case "queued":
      return (
        <span
          className="message-status queued"
          title="Queued"
        >
          ◷
        </span>
      );

    case "sending":
      return (
        <span
          className="message-status sending"
          title="Sending"
        >
          ◷
        </span>
      );

    case "sent":
      return (
        <span
          className="message-status sent"
          title="Sent"
        >
          ✓
        </span>
      );

    case "delivered":
      return (
        <span
          className="message-status delivered"
          title="Delivered"
        >
          ✓✓
        </span>
      );

    case "read":
      return (
        <span
          className="message-status read"
          title="Read"
        >
          ✓✓
        </span>
      );

    case "failed":
      return (
        <span
          className="message-status failed"
          title="Failed"
        >
          !
        </span>
      );

    default:
      return null;
  }
}

export default function MessageBubble({
  message,
}: MessageBubbleProps) {
  const outbound =
    message.direction === "outbound";

  return (
    <div
      className={`message-row ${
        outbound
          ? "outbound"
          : "inbound"
      }`}
    >
      <div className="message-bubble">

        <div className="message-text">
          {message.text}
        </div>

        <div className="message-meta">

          <span>
            {formatTime(
              message.created_at
            )}
          </span>

          {outbound && (
            <StatusIcon
              status={message.status}
            />
          )}

        </div>

      </div>
    </div>
  );
}