"use client";

import { useEffect, useState } from "react";
import { auth } from "../login/firebase";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function AdminPage() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<any[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const isAdmin = user && user.email === "threatdetectai@gmail.com";

  useEffect(() => {
    if (isAdmin) {
      fetchUsers();
    }
    // eslint-disable-next-line
  }, [isAdmin]);

  const fetchUsers = async () => {
    setUsersLoading(true);
    setError("");
    try {
      const res = await fetch("http://localhost:5000/api/users");
      if (!res.ok) throw new Error("Failed to fetch users");
      const data = await res.json();
      setUsers(data);
    } catch (err: any) {
      setError(err.message);
    }
    setUsersLoading(false);
  };

  const handleDelete = async (email: string) => {
    if (!window.confirm(`Delete user ${email}?`)) return;
    try {
      const res = await fetch(`http://localhost:5000/api/users/${email}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete user");
      await fetchUsers();
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) return <div>Loading...</div>;

  if (!user) {
    router.push("/login");
    return null;
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      {isAdmin ? (
        <>
          <p>Welcome, Admin!</p>
          <Link href="/logs" className="text-blue-600 underline">
            Go to Logs
          </Link>
          <Link href="/settings" className="text-blue-600 underline ml-4">
            Go to Settings
          </Link>
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-2">User Management</h2>
            {usersLoading ? (
              <p>Loading users...</p>
            ) : error ? (
              <p className="text-red-500">{error}</p>
            ) : (
              <table className="w-full border border-zinc-700 mt-2">
                <thead>
                  <tr className="bg-zinc-800 text-white">
                    <th className="p-2 border border-zinc-700">Username</th>
                    <th className="p-2 border border-zinc-700">Email</th>
                    <th className="p-2 border border-zinc-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u, idx) => (
                    <tr key={u._id || u.username || idx} className="bg-zinc-900 text-zinc-200">
                      <td className="p-2 border border-zinc-700">{u.username}</td>
                      <td className="p-2 border border-zinc-700">{u.email}</td>
                      <td className="p-2 border border-zinc-700">
                        <button
                          onClick={() => handleDelete(u.email)}
                          className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      ) : (
        <p>You do not have admin access.</p>
      )}
    </div>
  );
} 