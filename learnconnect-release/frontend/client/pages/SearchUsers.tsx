import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, UserPlus, Loader, Check, X, UserCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const BASE_URL = import.meta.env.VITE_BASE_URL;

interface User {
  id: number;
  name: string;
  email: string;
  profile_picture?: string;
  bio?: string;
  connection_status?: string;
}

export default function SearchUsers() {
  const [searchQuery, setSearchQuery] = useState("");
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
  }, [navigate]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setUsers([]);
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${BASE_URL}/api/users/search?q=${encodeURIComponent(searchQuery)}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) throw new Error("Failed to search users");

      const data = await response.json();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to search users");
    } finally {
      setLoading(false);
    }
  };

  const handleAddConnection = async (userId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    setActionLoading(userId);

    try {
      const response = await fetch(`${BASE_URL}/api/users/connections`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ addressee_id: userId }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to send connection request");
      }

      // Update the user's connection status
      setUsers(
        users.map((user) =>
          user.id === userId
            ? { ...user, connection_status: "pending" }
            : user
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send connection request");
    } finally {
      setActionLoading(null);
    }
  };

  const getConnectionButton = (user: User) => {
    const status = user.connection_status || "none";

    if (status === "accepted") {
      return (
        <Button disabled variant="outline" className="gap-2">
          <UserCheck className="w-4 h-4" />
          Connected
        </Button>
      );
    }

    if (status === "pending") {
      return (
        <Button disabled variant="outline" className="gap-2">
          <Loader className="w-4 h-4 animate-spin" />
          Pending
        </Button>
      );
    }

    if (status === "rejected" || status === "blocked") {
      return (
        <Button disabled variant="outline" className="gap-2">
          <X className="w-4 h-4" />
          {status === "blocked" ? "Blocked" : "Rejected"}
        </Button>
      );
    }

    return (
      <Button
        onClick={() => handleAddConnection(user.id)}
        disabled={actionLoading === user.id}
        className="gap-2"
      >
        {actionLoading === user.id ? (
          <>
            <Loader className="w-4 h-4 animate-spin" />
            Sending...
          </>
        ) : (
          <>
            <UserPlus className="w-4 h-4" />
            Add Connection
          </>
        )}
      </Button>
    );
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Search Users</h1>
        <p className="text-muted-foreground">
          Find and connect with other learners
        </p>
      </div>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
            <Input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or email..."
              className="pl-10"
            />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? (
              <>
                <Loader className="w-4 h-4 animate-spin mr-2" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Search
              </>
            )}
          </Button>
        </div>
      </form>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded-lg mb-8">
          {error}
        </div>
      )}

      {users.length === 0 && searchQuery && !loading ? (
        <Card>
          <CardContent className="py-12 text-center">
            <UserPlus className="w-16 h-16 text-muted-foreground opacity-50 mx-auto mb-4" />
            <p className="text-muted-foreground text-lg">
              No users found matching "{searchQuery}"
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {users.map((user) => (
            <Card key={user.id}>
              <CardHeader>
                <div className="flex items-center gap-4">
                  <Avatar className="w-16 h-16">
                    <AvatarImage src={user.profile_picture} />
                    <AvatarFallback className="text-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                      {getInitials(user.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <CardTitle className="text-lg">{user.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {user.bio && (
                  <p className="text-sm text-muted-foreground mb-4">{user.bio}</p>
                )}
                {getConnectionButton(user)}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!searchQuery && (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="w-16 h-16 text-muted-foreground opacity-50 mx-auto mb-4" />
            <p className="text-muted-foreground text-lg">
              Enter a name or email to search for users
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

