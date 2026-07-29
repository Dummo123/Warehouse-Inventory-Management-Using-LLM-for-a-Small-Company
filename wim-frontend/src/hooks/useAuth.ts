import { useState } from "react";
import { login as apiLogin } from "../api";

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const signIn = async (username: string, password: string) => {
    setLoading(true);
    setError("");
    try {
      const res = await apiLogin(username, password);
      localStorage.setItem("token", res.data.access_token);
      return true;
    } catch {
      setError("Неверный логин или пароль");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const signOut = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  return { signIn, signOut, loading, error };
}
