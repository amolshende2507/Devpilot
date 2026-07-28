"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg("");

    try {
      await apiFetch("/auth/signup", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      });
      router.push("/login?signup_success=true");
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred during signup.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-black p-4 font-sans overflow-hidden">
      {/* Sleek Radial Glow Background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.08),transparent_50%)]" />
      
      {/* High-tech Subtle Grid Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:24px_24px]" />

      <Card className="relative w-full max-w-md border-zinc-800/80 bg-zinc-950/60 backdrop-blur-md shadow-2xl">
        <CardHeader className="space-y-2 pb-6">
          <div className="flex justify-center mb-2">
            {/* Minimal Brand Logo */}
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 shadow-md shadow-indigo-500/20">
              <span className="font-mono text-xl font-black text-white">DP</span>
            </div>
          </div>
          <CardTitle className="text-2xl font-semibold tracking-tight text-center text-white">
            Create an account
          </CardTitle>
          <CardDescription className="text-center text-zinc-400 text-sm">
            Enter your details below to register for{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text font-semibold text-transparent">
              DevPilot AI
            </span>
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {errorMsg && (
              <div className="rounded-lg bg-red-950/30 p-3 text-sm text-red-400 border border-red-900/50">
                {errorMsg}
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="name" className="text-zinc-300 text-sm">Full Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="Amol Shende"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                disabled={isLoading}
                className="border-zinc-800 bg-zinc-900/40 text-white placeholder-zinc-500 focus:border-indigo-500 focus:ring-indigo-500/20 transition-all"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-zinc-300 text-sm">Email address</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                className="border-zinc-800 bg-zinc-900/40 text-white placeholder-zinc-500 focus:border-indigo-500 focus:ring-indigo-500/20 transition-all"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-zinc-300 text-sm">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                className="border-zinc-800 bg-zinc-900/40 text-white placeholder-zinc-500 focus:border-indigo-500 focus:ring-indigo-500/20 transition-all"
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4 pt-4">
            <Button 
              className="w-full bg-gradient-to-r from-indigo-500 to-violet-600 text-white hover:from-indigo-600 hover:to-violet-700 shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/20 transition-all duration-200" 
              type="submit" 
              disabled={isLoading}
            >
              {isLoading ? "Creating account..." : "Sign Up"}
            </Button>
            <div className="text-center text-xs text-zinc-500">
              Already have an account?{" "}
              <Link href="/login" className="text-zinc-300 hover:text-white underline transition-colors">
                Log in
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}