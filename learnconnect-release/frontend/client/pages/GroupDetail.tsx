import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Users, Share2, Loader, LogOut, UserPlus, UserCheck, X } from "lucide-react";
import { GroupChat } from "@/components/ui/GroupChat";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface GroupMember {
  id: number;
  name: string;
  email: string;
  profile_picture?: string;
  bio?: string;
  connection_status?: string;
}

interface GroupResource {
  id: number;
  title: string;
  url: string;
  resource_type: string;
  shared_by: number;
}

interface GroupData {
  id: number;
  title: string;
  description: string;
  topic_id: number;
  created_by: number;
  members: GroupMember[];
  resources: GroupResource[];
}

const BASE_URL = import.meta.env.VITE_BASE_URL;
console.log(BASE_URL);


export default function GroupDetail() {
  const { id } = useParams<{ id: string }>();
  const [group, setGroup] = useState<GroupData | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [membersLoading, setMembersLoading] = useState(false);
  const [error, setError] = useState("");
  const [showShareForm, setShowShareForm] = useState(false);
  const [shareData, setShareData] = useState({
    title: "",
    url: "",
    resource_type: "article",
  });
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }

    const fetchGroup = async () => {
      try {
        const response = await fetch(`${BASE_URL}/api/groups/${id}`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) throw new Error("Failed to fetch group");
        const data = await response.json();
        setGroup(data);
        
        // Fetch members with connection status
        fetchMembers();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load group");
      } finally {
        setLoading(false);
      }
    };

    const fetchMembers = async () => {
      const token = localStorage.getItem("token");
      if (!token) return;

      setMembersLoading(true);
      try {
        const response = await fetch(`${BASE_URL}/api/users/group/${id}/members`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setMembers(data);
        }
      } catch (err) {
        console.error("Failed to fetch members:", err);
      } finally {
        setMembersLoading(false);
      }
    };

    fetchGroup();
  }, [id, navigate]);

  const handleShareResource = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("token");

    try {
      const response = await fetch(`${BASE_URL}/api/groups/${id}/resources`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(shareData),
        },
      );

      if (!response.ok) throw new Error("Failed to share resource");

      setShareData({ title: "", url: "", resource_type: "article" });
      setShowShareForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to share resource");
    }
  };

  const handleLeaveGroup = async () => {
    const token = localStorage.getItem("token");

    try {
      const response = await fetch(`${BASE_URL}/api/groups/${id}/leave`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) throw new Error("Failed to leave group");
      navigate("/groups");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to leave group");
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

      // Update the member's connection status
      setMembers(
        members.map((member) =>
          member.id === userId
            ? { ...member, connection_status: "pending" }
            : member
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send connection request");
    } finally {
      setActionLoading(null);
    }
  };

  const getConnectionButton = (member: GroupMember) => {
    const status = member.connection_status || "none";

    if (status === "accepted") {
      return (
        <Button disabled variant="outline" size="sm" className="gap-1">
          <UserCheck className="w-3 h-3" />
          Connected
        </Button>
      );
    }

    if (status === "pending") {
      return (
        <Button disabled variant="outline" size="sm" className="gap-1">
          <Loader className="w-3 h-3 animate-spin" />
          Pending
        </Button>
      );
    }

    if (status === "rejected" || status === "blocked") {
      return (
        <Button disabled variant="outline" size="sm" className="gap-1">
          <X className="w-3 h-3" />
          {status === "blocked" ? "Blocked" : "Rejected"}
        </Button>
      );
    }

    return (
      <Button
        onClick={() => handleAddConnection(member.id)}
        disabled={actionLoading === member.id}
        size="sm"
        className="gap-1"
      >
        {actionLoading === member.id ? (
          <>
            <Loader className="w-3 h-3 animate-spin" />
            Sending...
          </>
        ) : (
          <>
            <UserPlus className="w-3 h-3" />
            Connect
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

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!group) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded-lg">
          {error || "Group not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">{group.title}</h1>
        <p className="text-muted-foreground">{group.description}</p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded-lg mb-8">
          {error}
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-8 mb-12">
        <div className="md:col-span-2">
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Share2 className="w-6 h-6" />
                Shared Resources
              </h2>
              <button
                onClick={() => setShowShareForm(!showShareForm)}
                className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold hover:opacity-90"
              >
                Share Resource
              </button>
            </div>

            {showShareForm && (
              <form
                onSubmit={handleShareResource}
                className="bg-card rounded-lg border border-border p-6 mb-6 space-y-4"
              >
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Resource Title
                  </label>
                  <input
                    type="text"
                    value={shareData.title}
                    onChange={(e) =>
                      setShareData({ ...shareData, title: e.target.value })
                    }
                    placeholder="e.g., Awesome React Tutorial"
                    className="w-full px-4 py-2 rounded-lg border border-input bg-background"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Resource URL
                  </label>
                  <input
                    type="url"
                    value={shareData.url}
                    onChange={(e) =>
                      setShareData({ ...shareData, url: e.target.value })
                    }
                    placeholder="https://..."
                    className="w-full px-4 py-2 rounded-lg border border-input bg-background"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Type</label>
                  <select
                    value={shareData.resource_type}
                    onChange={(e) =>
                      setShareData({
                        ...shareData,
                        resource_type: e.target.value,
                      })
                    }
                    className="w-full px-4 py-2 rounded-lg border border-input bg-background"
                  >
                    <option value="article">Article</option>
                    <option value="youtube">YouTube Video</option>
                    <option value="course">Course</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="flex gap-4">
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold hover:opacity-90"
                  >
                    Share
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowShareForm(false)}
                    className="px-4 py-2 rounded-lg border border-border hover:bg-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}

            <div className="space-y-4">
              {group.resources.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No resources shared yet
                </p>
              ) : (
                group.resources.map((resource) => (
                  <a
                    key={resource.id}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block bg-card rounded-lg border border-border p-4 hover:border-primary transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold hover:text-primary transition-colors">
                          {resource.title}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          Type: {resource.resource_type}
                        </p>
                      </div>
                      <span className="text-xs bg-secondary px-2 py-1 rounded">
                        {resource.resource_type}
                      </span>
                    </div>
                  </a>
                ))
              )}
            </div>
          </div>
          <div className="mb-8">
            <GroupChat groupId={group.id} />
          </div>

        </div>

        <div>
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Users className="w-5 h-5" />
              Members ({group.members.length})
            </h2>
            {membersLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader className="w-6 h-6 animate-spin" />
              </div>
            ) : (
              <div className="space-y-3 mb-6">
                {members.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No other members in this group
                  </p>
                ) : (
                  members.map((member) => (
                    <div
                      key={member.id}
                      className="py-3 border-b border-border last:border-0 flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <Avatar className="w-10 h-10">
                          <AvatarImage src={member.profile_picture} />
                          <AvatarFallback className="text-xs bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                            {getInitials(member.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm truncate">{member.name}</p>
                          <p className="text-xs text-muted-foreground truncate">
                            {member.email}
                          </p>
                        </div>
                      </div>
                      {getConnectionButton(member)}
                    </div>
                  ))
                )}
              </div>
            )}

            <button
              onClick={handleLeaveGroup}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors font-semibold"
            >
              <LogOut className="w-4 h-4" />
              Leave Group
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
