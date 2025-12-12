import { useState, useEffect, useRef, useCallback } from "react";
import { Send, Wifi, WifiOff } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface Message {
  id: number;
  content: string;
  user_id: number;
  created_at: string;
  user: {
    name: string;
    profile_picture?: string;
  };
}

interface GroupChatProps {
  groupId: number;
}

type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

export function GroupChat({ groupId }: GroupChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const scrollBottomRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch initial messages via REST API
  const fetchInitialMessages = useCallback(async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8058/api/groups/${groupId}/messages`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      }
    } catch (error) {
      console.error("Failed to fetch initial messages", error);
    }
  }, [groupId]);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No auth token found");
      setConnectionStatus("error");
      return;
    }

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    setConnectionStatus("connecting");

    // Create WebSocket connection
    const ws = new WebSocket(
      `ws://localhost:8058/api/groups/${groupId}/ws?token=${token}`
    );

    ws.onopen = () => {
      console.log("WebSocket connected");
      setConnectionStatus("connected");
      // Clear any pending reconnection attempts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      const newMsg: Message = JSON.parse(event.data);
      setMessages((prev) => {
        // Avoid duplicates
        if (prev.some((m) => m.id === newMsg.id)) {
          return prev;
        }
        return [...prev, newMsg];
      });
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnectionStatus("error");
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setConnectionStatus("disconnected");
      wsRef.current = null;

      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log("Attempting to reconnect...");
        connectWebSocket();
      }, 3000);
    };

    wsRef.current = ws;
  }, [groupId]);

  // Initialize: fetch messages and connect WebSocket
  useEffect(() => {
    fetchInitialMessages();
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [fetchInitialMessages, connectWebSocket]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !wsRef.current || connectionStatus !== "connected") {
      return;
    }

    // Send message via WebSocket
    wsRef.current.send(
      JSON.stringify({
        content: newMessage,
      })
    );

    setNewMessage("");
  };

  // Connection status indicator
  const getStatusIcon = () => {
    switch (connectionStatus) {
      case "connected":
        return <Wifi className="w-4 h-4 text-green-500" />;
      case "connecting":
        return <Wifi className="w-4 h-4 text-yellow-500 animate-pulse" />;
      case "disconnected":
      case "error":
        return <WifiOff className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      case "disconnected":
        return "Disconnected";
      case "error":
        return "Connection Error";
    }
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Group Chat</CardTitle>
        <div className="flex items-center gap-2 text-sm">
          {getStatusIcon()}
          <span className="text-muted-foreground">{getStatusText()}</span>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div key={message.id} className="flex gap-3">
                <Avatar>
                  <AvatarImage src={message.user.profile_picture || undefined} />
                  <AvatarFallback>{message.user.name[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">{message.user.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(message.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ))}
            <div ref={scrollBottomRef} />
          </div>
        </ScrollArea>
        <div className="p-4 border-t">
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <Input
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder={
                connectionStatus === "connected"
                  ? "Type a message..."
                  : "Connecting..."
              }
              className="flex-1"
              disabled={connectionStatus !== "connected"}
            />
            <Button
              type="submit"
              size="icon"
              disabled={connectionStatus !== "connected"}
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}
