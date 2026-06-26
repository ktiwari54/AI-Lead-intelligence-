/**
 * Real-time notification hooks using WebSocket + react-query.
 */
import { useEffect, useRef, useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post, del } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Notification, PaginatedResponse } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1";

// ─── HTTP hooks ──────────────────────────────────────────────────────────────

export function useNotifications(unreadOnly = false, page = 1) {
  return useQuery({
    queryKey: ["notifications", { unreadOnly, page }],
    queryFn: () =>
      get<PaginatedResponse<Notification>>(
        `/notifications?unread_only=${unreadOnly}&page=${page}`
      ),
    refetchInterval: 60_000, // poll every minute as fallback
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => get<{ unread_count: number }>("/notifications/unread-count"),
    refetchInterval: 30_000,
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (notificationIds: string[]) =>
      post("/notifications/mark-read", { notification_ids: notificationIds }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => post("/notifications/mark-all-read", {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useDeleteNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => del(`/notifications/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

// ─── WebSocket hook ───────────────────────────────────────────────────────────

export type WSMessage =
  | { type: "connected"; user_id: string; timestamp: string }
  | { type: "notification"; data: Notification; timestamp: string }
  | { type: "ping" }
  | { type: "pong"; timestamp: string };

export type WSStatus = "connecting" | "connected" | "disconnected" | "error";

export function useNotificationWebSocket(options?: {
  onNotification?: (n: Notification) => void;
  autoReconnect?: boolean;
}) {
  const { onNotification, autoReconnect = true } = options ?? {};
  const qc = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const [status, setStatus] = useState<WSStatus>("disconnected");
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  const connect = useCallback(() => {
    const token = getToken();
    if (!token || wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const ws = new WebSocket(`${WS_URL}/notifications/ws?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        setLastMessage(msg);

        if (msg.type === "ping") {
          ws.send(JSON.stringify({ type: "pong" }));
        } else if (msg.type === "notification") {
          // Invalidate react-query cache so lists refresh
          qc.invalidateQueries({ queryKey: ["notifications"] });
          onNotification?.(msg.data);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      setStatus("error");
    };

    ws.onclose = () => {
      setStatus("disconnected");
      wsRef.current = null;

      if (autoReconnect && reconnectAttempts.current < 5) {
        const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30_000);
        reconnectAttempts.current += 1;
        reconnectTimer.current = setTimeout(connect, delay);
      }
    };
  }, [onNotification, autoReconnect, qc]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("disconnected");
  }, []);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "ping" }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { status, lastMessage, connect, disconnect, sendPing };
}
