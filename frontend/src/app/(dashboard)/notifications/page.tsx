"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post, patch, del } from "@/lib/api";

// ---- Types ----
interface Notification {
  id: string;
  title: string;
  message: string;
  channel: "IN_APP" | "EMAIL" | "WEBHOOK";
  is_read: boolean;
  created_at: string;
}

interface NotificationsResponse {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
}

// ---- Hooks ----
function useNotifications(page: number, filter: "all" | "unread") {
  return useQuery({
    queryKey: ["notifications", page, filter],
    queryFn: () =>
      get<NotificationsResponse>(`/notifications?page=${page}&page_size=20${filter === "unread" ? "&is_read=false" : ""}`),
    refetchInterval: 30000,
  });
}

function useUnreadCount() {
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => get<{ data: { count: number } }>("/notifications/unread-count").then(r => r.data?.count ?? 0),
    refetchInterval: 30000,
  });
}

function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => patch(`/notifications/${id}/read`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => post("/notifications/read-all", {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

function useDeleteNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => del(`/notifications/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

function useNotificationWebSocket(onNewNotification: (n: Notification) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      try {
        const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
        ws = new WebSocket(`${proto}//${window.location.host}/api/v1/notifications/ws`);
        wsRef.current = ws;

        ws.onopen = () => setConnected(true);
        ws.onclose = () => {
          setConnected(false);
          reconnectTimer = setTimeout(connect, 5000);
        };
        ws.onerror = () => { setConnected(false); ws.close(); };
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "notification" && data.notification) {
              onNewNotification(data.notification);
            }
          } catch {
            // ignore parse errors
          }
        };
      } catch {
        reconnectTimer = setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [onNewNotification]);

  return { connected };
}

// ---- Helpers ----
function relativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return "Just now";
  if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? "" : "s"} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? "" : "s"} ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

const CHANNEL_COLORS: Record<string, string> = {
  IN_APP: "bg-blue-500",
  EMAIL: "bg-green-500",
  WEBHOOK: "bg-purple-500",
};

const CHANNEL_ICONS: Record<string, string> = {
  IN_APP: "🔔",
  EMAIL: "✉",
  WEBHOOK: "🔗",
};

// ---- Toast ----
interface ToastProps {
  notification: Notification;
  onDismiss: () => void;
}

function Toast({ notification, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 5000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div className="bg-white border border-gray-200 shadow-lg rounded-xl p-4 flex items-start gap-3 max-w-sm animate-in slide-in-from-right">
      <div className={`w-8 h-8 rounded-full ${CHANNEL_COLORS[notification.channel] ?? "bg-gray-400"} flex items-center justify-center text-white text-xs shrink-0`}>
        {CHANNEL_ICONS[notification.channel] ?? "🔔"}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-gray-900 truncate">{notification.title}</p>
        <p className="text-xs text-gray-500 line-clamp-2">{notification.message}</p>
      </div>
      <button onClick={onDismiss} className="text-gray-400 hover:text-gray-600 shrink-0 text-lg leading-none">&times;</button>
    </div>
  );
}

// ---- Main Page ----
export default function NotificationsPage() {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<"all" | "unread">("all");
  const [toasts, setToasts] = useState<Notification[]>([]);

  const { data, isLoading, error } = useNotifications(page, filter);
  const { data: unreadCount } = useUnreadCount();
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();
  const deleteNotification = useDeleteNotification();

  const handleNewNotification = useCallback((n: Notification) => {
    setToasts(prev => [...prev, n]);
  }, []);

  const { connected } = useNotificationWebSocket(handleNewNotification);

  const notifications = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageSize = data?.page_size ?? 20;
  const totalPages = Math.ceil(total / pageSize);

  const handleClick = (notification: Notification) => {
    if (!notification.is_read) {
      markRead.mutate(notification.id);
    }
  };

  return (
    <div className="max-w-3xl">
      {/* Toast container */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map(n => (
          <Toast key={n.id} notification={n} onDismiss={() => setToasts(prev => prev.filter(t => t.id !== n.id))} />
        ))}
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
          {unreadCount != null && unreadCount > 0 && (
            <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {unreadCount}
            </span>
          )}
          {connected && (
            <span className="flex items-center gap-1.5 text-xs text-green-600 font-medium">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Live
            </span>
          )}
        </div>
        <button
          onClick={() => markAllRead.mutate()}
          disabled={markAllRead.isPending}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          {markAllRead.isPending ? "Marking..." : "Mark All Read"}
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {(["all", "unread"] as const).map(f => (
          <button
            key={f}
            onClick={() => { setFilter(f); setPage(1); }}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors capitalize ${
              filter === f
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="text-center py-12 text-red-600">
          Failed to load notifications. Please try again.
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && notifications.length === 0 && (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">🔔</div>
          <h2 className="text-lg font-semibold text-gray-700 mb-1">No notifications yet</h2>
          <p className="text-gray-400 text-sm">When you receive notifications, they'll appear here.</p>
        </div>
      )}

      {/* Notification list */}
      {!isLoading && !error && notifications.length > 0 && (
        <div className="space-y-1">
          {notifications.map(notification => (
            <div
              key={notification.id}
              onClick={() => handleClick(notification)}
              className={`group relative flex items-start gap-4 px-4 py-4 rounded-xl cursor-pointer transition-colors ${
                notification.is_read ? "bg-white hover:bg-gray-50" : "bg-blue-50 hover:bg-blue-100"
              }`}
            >
              {/* Channel icon */}
              <div className={`w-9 h-9 rounded-full ${CHANNEL_COLORS[notification.channel] ?? "bg-gray-400"} flex items-center justify-center text-white text-sm shrink-0`}>
                {CHANNEL_ICONS[notification.channel] ?? "🔔"}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className={`text-sm ${notification.is_read ? "text-gray-800 font-normal" : "text-gray-900 font-semibold"} truncate`}>
                  {notification.title}
                </p>
                <p className="text-sm text-gray-500 line-clamp-2 mt-0.5">{notification.message}</p>
                <p className="text-xs text-gray-400 mt-1">{relativeTime(notification.created_at)}</p>
              </div>

              {/* Unread dot + delete */}
              <div className="flex items-center gap-2 shrink-0">
                {!notification.is_read && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); deleteNotification.mutate(notification.id); }}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 text-lg leading-none transition-opacity"
                  aria-label="Delete notification"
                >
                  &times;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <div className="flex gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (page <= 3) {
                pageNum = i + 1;
              } else if (page >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = page - 2 + i;
              }
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-8 h-8 text-sm rounded-lg ${pageNum === page ? "bg-indigo-600 text-white" : "text-gray-700 hover:bg-gray-100"}`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
