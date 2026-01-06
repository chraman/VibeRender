"use client";

import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  const handleLogin = () => {
    // ⚠️ TEMP auth simulation
    document.cookie = "token=fake-jwt; path=/";

    // Redirect after login
    router.push("/dashboard");
  };

  return (
    <div className="bg-white p-6 rounded shadow w-80">
      <h1 className="text-xl font-semibold mb-4">Login</h1>

      <button
        onClick={handleLogin}
        className="w-full bg-black text-white py-2 rounded"
      >
        Login
      </button>
    </div>
  );
}
