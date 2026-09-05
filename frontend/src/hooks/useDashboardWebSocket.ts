import { useEffect, useRef } from "react";
import type { Message } from "../types/chat";

export interface DashboardEvent {
  type: string;
  conversation_id?: number;
  message?: Message;
  [key: string]: unknown;
}

interface UseDashboardWebSocketOptions {
  onEvent?: (event: DashboardEvent) => void;
}

export default function useDashboardWebSocket({
  onEvent,
}: UseDashboardWebSocketOptions) {
  const socketRef = useRef<WebSocket | null>(null);
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    const protocol =
      window.location.protocol === "https:" ? "wss" : "ws";

    const host = window.location.hostname;

    const socket = new WebSocket(
      `${protocol}://${host}:8000/ws/dashboard/`
    );

    socketRef.current = socket;

    socket.onopen = () => {
      console.log("Dashboard WebSocket connected.");
    };

    socket.onmessage = (event) => {
      try {
        const data: DashboardEvent = JSON.parse(event.data);

        console.log("Dashboard WebSocket event:", data);

        onEventRef.current?.(data);
      } catch (error) {
        console.error(
          "Failed to parse WebSocket event:",
          error
        );
      }
    };

    socket.onerror = (error) => {
      console.error(
        "Dashboard WebSocket error:",
        error
      );
    };

    socket.onclose = (event) => {
      console.log(
        "Dashboard WebSocket closed:",
        event.code,
        event.reason
      );
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, []);

  return socketRef;
}