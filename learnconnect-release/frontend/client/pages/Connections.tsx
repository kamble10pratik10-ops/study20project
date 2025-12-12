import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  UserCheck,
  UserPlus,
  Loader,
  Check,
  X,
  Trash2,
  Users,
  UserX,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const BASE_URL = import.meta.env.VITE_BASE_URL;

interface Connection {
  id: number;
  requester_id: number;
  addressee_id: number;
  status: string;
  created_at: string;
  updated_at: string;
  requester: {
    id: number;
    name: string;
    email: string;
    profile_picture?: string;
  };
  addressee: {
    id: number;
    name: string;
    email: string;
    profile_picture?: string;
  };
}

export default function Connections() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }

    fetchConnections();
  }, [navigate]);

  const fetchConnections = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${BASE_URL}/api/users/connections`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch connections");

      const data = await response.json();
      setConnections(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load connections");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateConnection = async (
    connectionId: number,
    status: string
  ) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    setActionLoading(connectionId);

    try {
      const response = await fetch(
        `${BASE_URL}/api/users/connections/${connectionId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ status }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update connection");
      }

      await fetchConnections();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update connection");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteConnection = async (connectionId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    if (!confirm("Are you sure you want to remove this connection?")) {
      return;
    }

    setActionLoading(connectionId);

    try {
      const response = await fetch(
        `${BASE_URL}/api/users/connections/${connectionId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to delete connection");
      }

      await fetchConnections();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete connection");
    } finally {
      setActionLoading(null);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const getCurrentUserId = () => {
    const user = localStorage.getItem("user");
    if (user) {
      return JSON.parse(user).id;
    }
    return null;
  };

  const getOtherUser = (connection: Connection) => {
    const currentUserId = getCurrentUserId();
    return connection.requester_id === currentUserId
      ? connection.addressee
      : connection.requester;
  };

  const isRequester = (connection: Connection) => {
    const currentUserId = getCurrentUserId();
    return connection.requester_id === currentUserId;
  };

  const pendingReceived = connections.filter(
    (c) => c.status === "pending" && !isRequester(c)
  );
  const pendingSent = connections.filter(
    (c) => c.status === "pending" && isRequester(c)
  );
  const accepted = connections.filter((c) => c.status === "accepted");
  const rejected = connections.filter((c) => c.status === "rejected");
  const blocked = connections.filter((c) => c.status === "blocked");

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Connections</h1>
        <p className="text-muted-foreground">
          Manage your connections and connection requests
        </p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded-lg mb-8">
          {error}
        </div>
      )}

      <Tabs defaultValue="received" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="received">
            Received ({pendingReceived.length})
          </TabsTrigger>
          <TabsTrigger value="sent">
            Sent ({pendingSent.length})
          </TabsTrigger>
          <TabsTrigger value="accepted">
            Connected ({accepted.length})
          </TabsTrigger>
          <TabsTrigger value="all">All ({connections.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="received" className="mt-6">
          {pendingReceived.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <UserPlus className="w-16 h-16 text-muted-foreground opacity-50 mx-auto mb-4" />
                <p className="text-muted-foreground text-lg">
                  No pending connection requests
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pendingReceived.map((connection) => {
                const otherUser = getOtherUser(connection);
                return (
                  <Card key={connection.id}>
                    <CardHeader>
                      <div className="flex items-center gap-4">
                        <Avatar className="w-16 h-16">
                          <AvatarImage src={otherUser.profile_picture} />
                          <AvatarFallback className="text-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                            {getInitials(otherUser.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <CardTitle className="text-lg">{otherUser.name}</CardTitle>
                          <p className="text-sm text-muted-foreground">
                            {otherUser.email}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex gap-2">
                        <Button
                          onClick={() =>
                            handleUpdateConnection(connection.id, "accepted")
                          }
                          disabled={actionLoading === connection.id}
                          className="flex-1 gap-2"
                        >
                          {actionLoading === connection.id ? (
                            <>
                              <Loader className="w-4 h-4 animate-spin" />
                              Processing...
                            </>
                          ) : (
                            <>
                              <Check className="w-4 h-4" />
                              Accept
                            </>
                          )}
                        </Button>
                        <Button
                          onClick={() =>
                            handleUpdateConnection(connection.id, "rejected")
                          }
                          disabled={actionLoading === connection.id}
                          variant="outline"
                          className="flex-1 gap-2"
                        >
                          <X className="w-4 h-4" />
                          Reject
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="sent" className="mt-6">
          {pendingSent.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <UserPlus className="w-16 h-16 text-muted-foreground opacity-50 mx-auto mb-4" />
                <p className="text-muted-foreground text-lg">
                  No pending sent requests
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pendingSent.map((connection) => {
                const otherUser = getOtherUser(connection);
                return (
                  <Card key={connection.id}>
                    <CardHeader>
                      <div className="flex items-center gap-4">
                        <Avatar className="w-16 h-16">
                          <AvatarImage src={otherUser.profile_picture} />
                          <AvatarFallback className="text-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                            {getInitials(otherUser.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <CardTitle className="text-lg">{otherUser.name}</CardTitle>
                          <p className="text-sm text-muted-foreground">
                            {otherUser.email}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          Request pending
                        </span>
                        <Button
                          onClick={() => handleDeleteConnection(connection.id)}
                          disabled={actionLoading === connection.id}
                          variant="outline"
                          size="sm"
                          className="gap-2"
                        >
                          {actionLoading === connection.id ? (
                            <>
                              <Loader className="w-3 h-3 animate-spin" />
                            </>
                          ) : (
                            <>
                              <Trash2 className="w-3 h-3" />
                              Cancel
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="accepted" className="mt-6">
          {accepted.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Users className="w-16 h-16 text-muted-foreground opacity-50 mx-auto mb-4" />
                <p className="text-muted-foreground text-lg">
                  No connections yet
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {accepted.map((connection) => {
                const otherUser = getOtherUser(connection);
                return (
                  <Card key={connection.id}>
                    <CardHeader>
                      <div className="flex items-center gap-4">
                        <Avatar className="w-16 h-16">
                          <AvatarImage src={otherUser.profile_picture} />
                          <AvatarFallback className="text-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                            {getInitials(otherUser.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <CardTitle className="text-lg">{otherUser.name}</CardTitle>
                          <p className="text-sm text-muted-foreground">
                            {otherUser.email}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                          <UserCheck className="w-4 h-4" />
                          Connected
                        </div>
                        <Button
                          onClick={() => handleDeleteConnection(connection.id)}
                          disabled={actionLoading === connection.id}
                          variant="outline"
                          size="sm"
                          className="gap-2"
                        >
                          {actionLoading === connection.id ? (
                            <>
                              <Loader className="w-3 h-3 animate-spin" />
                            </>
                          ) : (
                            <>
                              <Trash2 className="w-3 h-3" />
                              Remove
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="all" className="mt-6">
          {connections.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Users className="w-16 h-16 text-muted-foreground opacity-50 mx-auto mb-4" />
                <p className="text-muted-foreground text-lg">
                  No connections yet
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {connections.map((connection) => {
                const otherUser = getOtherUser(connection);
                const statusColors: Record<string, string> = {
                  accepted: "text-green-600 dark:text-green-400",
                  pending: "text-yellow-600 dark:text-yellow-400",
                  rejected: "text-red-600 dark:text-red-400",
                  blocked: "text-gray-600 dark:text-gray-400",
                };
                return (
                  <Card key={connection.id}>
                    <CardHeader>
                      <div className="flex items-center gap-4">
                        <Avatar className="w-16 h-16">
                          <AvatarImage src={otherUser.profile_picture} />
                          <AvatarFallback className="text-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                            {getInitials(otherUser.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <CardTitle className="text-lg">{otherUser.name}</CardTitle>
                          <p className="text-sm text-muted-foreground">
                            {otherUser.email}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-sm capitalize ${statusColors[connection.status] || "text-muted-foreground"}`}
                        >
                          {connection.status}
                        </span>
                        {connection.status !== "blocked" && (
                          <Button
                            onClick={() => handleDeleteConnection(connection.id)}
                            disabled={actionLoading === connection.id}
                            variant="outline"
                            size="sm"
                            className="gap-2"
                          >
                            {actionLoading === connection.id ? (
                              <>
                                <Loader className="w-3 h-3 animate-spin" />
                              </>
                            ) : (
                              <>
                                <Trash2 className="w-3 h-3" />
                                Remove
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

