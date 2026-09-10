import { useEffect, useRef } from "react";
import type { Message } from "../types/chat";
import type {
  CampaignStatistics,
  CampaignStatus,
} from "../types/campaign";

/* =========================================================
   EVENT TYPES
   ========================================================= */

export interface DashboardCampaignEvent {
  id: number;
  name: string;
  status: CampaignStatus;
  statistics: CampaignStatistics & {
    queued?: number;
  };
  created_at?: string | null;
  updated_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface DashboardAudienceEvent {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  member_count: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface DashboardEvent {
  type: string;

  conversation_id?: number;
  message?: Message;

  campaign_id?: number;
  campaign?: DashboardCampaignEvent;

  recipient?: Record<string, unknown> | null;

  audience_id?: number;
  audience?: DashboardAudienceEvent;

  customer_id?: number;
  customer?: Record<string, unknown>;

  template_id?: number;
  template?: Record<string, unknown>;

  [key: string]: unknown;
}

/* =========================================================
   OPTIONS
   ========================================================= */

interface UseDashboardWebSocketOptions {
  onEvent?: (event: DashboardEvent) => void;
}

/* =========================================================
   SHARED SOCKET
   ========================================================= */

const listeners = new Set<
  (event: DashboardEvent) => void
>();

let socket: WebSocket | null = null;

let reconnectTimer: number | null = null;

let reconnectDelay = 1000;

let intentionallyClosed = false;

/* =========================================================
   SOCKET URL
   ========================================================= */

function socketUrl(): string {
  const protocol =
    window.location.protocol === "https:"
      ? "wss"
      : "ws";

  return `${protocol}://${window.location.hostname}:8000/ws/dashboard/`;
}

/* =========================================================
   EVENT BROADCAST
   ========================================================= */

function notify(event: DashboardEvent) {
  listeners.forEach((listener) => {
    try {
      listener(event);
    } catch (error) {
      console.error(
        "Dashboard WebSocket listener error:",
        error,
      );
    }
  });
}

/* =========================================================
   RECONNECT
   ========================================================= */

function scheduleReconnect() {
  if (
    intentionallyClosed ||
    reconnectTimer !== null ||
    listeners.size === 0
  ) {
    return;
  }

  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, reconnectDelay);

  reconnectDelay = Math.min(
    reconnectDelay * 2,
    10000,
  );
}

/* =========================================================
   CONNECT
   ========================================================= */

function connect() {
  if (
    intentionallyClosed ||
    listeners.size === 0
  ) {
    return;
  }

  if (
    socket &&
    (
      socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING
    )
  ) {
    return;
  }

  const nextSocket = new WebSocket(
    socketUrl(),
  );

  socket = nextSocket;

  nextSocket.onopen = () => {
    reconnectDelay = 1000;

    console.log(
      "Dashboard WebSocket connected.",
    );
  };

  nextSocket.onmessage = (event) => {
    try {
      const data: DashboardEvent =
        JSON.parse(event.data);

      console.log(
        "Dashboard WebSocket event:",
        data.type,
        data,
      );

      notify(data);
    } catch (error) {
      console.error(
        "Failed to parse Dashboard WebSocket event:",
        error,
      );
    }
  };

  nextSocket.onerror = (error) => {
    console.error(
      "Dashboard WebSocket error:",
      error,
    );
  };

  nextSocket.onclose = (event) => {
    if (socket === nextSocket) {
      socket = null;
    }

    console.log(
      "Dashboard WebSocket closed:",
      event.code,
      event.reason,
    );

    scheduleReconnect();
  };
}

/* =========================================================
   DISCONNECT WHEN NO SUBSCRIBERS
   ========================================================= */

function disconnectIfUnused() {
  if (listeners.size !== 0) {
    return;
  }

  intentionallyClosed = true;

  if (reconnectTimer !== null) {
    window.clearTimeout(
      reconnectTimer,
    );

    reconnectTimer = null;
  }

  if (socket) {
    socket.close();
    socket = null;
  }

  intentionallyClosed = false;
}

/* =========================================================
   HOOK
   ========================================================= */

export default function useDashboardWebSocket({
  onEvent,
}: UseDashboardWebSocketOptions) {
  const onEventRef =
    useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    const listener = (
      event: DashboardEvent,
    ) => {
      onEventRef.current?.(event);
    };

    listeners.add(listener);

    connect();

    return () => {
      listeners.delete(listener);

      disconnectIfUnused();
    };
  }, []);

  return null;
}