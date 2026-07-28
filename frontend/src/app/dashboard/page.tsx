"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Project {
  id: string;
  name: string;
  github_url: string;
  status: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isImporting, setIsImporting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // 1. Fetch user's indexed projects on load
  const fetchProjects = async () => {
    try {
      const data = await apiFetch<Project[]>("/projects");
      setProjects(data);
    } catch (err: any) {
      // If token is invalid or expired, redirect them back to login
      if (err.message.includes("401") || err.message.includes("expired")) {
        localStorage.removeItem("devpilot_token");
        router.push("/login");
      } else {
        setErrorMsg("Failed to retrieve repository index.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  // 2. Handle new repository import submission
  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsImporting(true);
    setErrorMsg("");

    try {
      const newProject = await apiFetch<Project>("/projects/import", {
        method: "POST",
        body: JSON.stringify({ name, github_url: githubUrl }),
      });
      
      // Update local state and reset inputs
      setProjects((prev) => [newProject, ...prev]);
      setName("");
      setGithubUrl("");
    } catch (err: any) {
      setErrorMsg(err.message || "Ingestion pipeline triggered an error.");
    } finally {
      setIsImporting(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("devpilot_token");
    router.push("/login");
  };

  return (
    <div className="relative min-h-screen bg-black text-white overflow-hidden font-sans">
      {/* Background Radial Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(99,102,241,0.05),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:32px_32px]" />

      {/* Global Header */}
      <header className="relative z-10 border-b border-zinc-800/80 bg-zinc-950/40 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 font-mono text-base font-black text-white">
            DP
          </div>
          <span className="font-semibold text-lg tracking-tight bg-gradient-to-r from-zinc-100 to-zinc-400 bg-clip-text text-transparent">
            DevPilot AI Dashboard
          </span>
        </div>
        <Button variant="ghost" onClick={handleLogout} className="text-zinc-400 hover:text-white hover:bg-zinc-900">
          Logout
        </Button>
      </header>

      {/* Main Workspace */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Repository Importer */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="border-zinc-800/80 bg-zinc-950/60 backdrop-blur-md">
            <CardHeader>
              <CardTitle className="text-lg text-white">Import Codebase</CardTitle>
              <CardDescription className="text-zinc-400 text-sm">
                Add a public GitHub URL to run our cloning, indexing, and vectorization pipelines.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleImport}>
              <CardContent className="space-y-4">
                {errorMsg && (
                  <div className="rounded-lg bg-red-950/30 p-3 text-sm text-red-400 border border-red-900/50">
                    {errorMsg}
                  </div>
                )}
                <div className="space-y-1.5">
                  <Label htmlFor="proj-name" className="text-zinc-300">Project Label</Label>
                  <Input
                    id="proj-name"
                    type="text"
                    placeholder="campuslife-os"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    disabled={isImporting}
                    className="border-zinc-800 bg-zinc-900/40 text-white placeholder-zinc-600 focus:border-indigo-500 focus:ring-indigo-500/20"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="git-url" className="text-zinc-300">GitHub Ingest URL</Label>
                  <Input
                    id="git-url"
                    type="url"
                    placeholder="https://github.com/..."
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                    required
                    disabled={isImporting}
                    className="border-zinc-800 bg-zinc-900/40 text-white placeholder-zinc-600 focus:border-indigo-500 focus:ring-indigo-500/20"
                  />
                </div>
              </CardContent>
              <CardFooter>
                <Button 
                  className="w-full bg-gradient-to-r from-indigo-500 to-violet-600 text-white hover:from-indigo-600 hover:to-violet-700 shadow-lg shadow-indigo-500/10" 
                  type="submit" 
                  disabled={isImporting}
                >
                  {isImporting ? "Indexing codebase..." : "Import Repository"}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>

        {/* Right Column: Codebase Indexes Grid */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold tracking-tight">Your Codebase Indexes</h2>
            <span className="text-xs text-zinc-500 font-mono">
              Total: {projects.length}
            </span>
          </div>

          {isLoading ? (
            <div className="text-sm text-zinc-500 py-12 text-center font-mono">
              Loading secure repository registers...
            </div>
          ) : projects.length === 0 ? (
            <div className="rounded-xl border border-dashed border-zinc-800 p-12 text-center text-zinc-500 bg-zinc-950/20">
              No registered repositories found. Use the importer on the left to index your first codebase.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {projects.map((project) => (
                <Card key={project.id} className="border-zinc-800/80 bg-zinc-950/40 hover:bg-zinc-950/70 hover:border-zinc-700/80 transition-all duration-200 flex flex-col justify-between">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono text-zinc-500 overflow-hidden text-ellipsis max-w-[120px]">
                        ID: {project.id.slice(0, 8)}...
                      </span>
                      {/* Interactive Status Badges */}
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                        project.status === "completed"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : project.status === "failed"
                          ? "bg-red-500/10 text-red-400 border-red-500/20"
                          : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20 animate-pulse"
                      }`}>
                        {project.status}
                      </span>
                    </div>
                    <CardTitle className="text-base font-semibold text-white truncate">
                      {project.name}
                    </CardTitle>
                    <CardDescription className="text-xs text-zinc-500 truncate hover:text-zinc-400 transition-colors">
                      <a href={project.github_url} target="_blank" rel="noopener noreferrer">
                        {project.github_url}
                      </a>
                    </CardDescription>
                  </CardHeader>
                  <CardFooter className="pt-2 border-t border-zinc-900/60 flex items-center justify-between space-x-2">
                    <Button 
                      variant="ghost" 
                      className="w-1/2 text-xs text-zinc-400 hover:text-white hover:bg-zinc-900/80"
                      disabled={project.status !== "completed"}
                    >
                      AI Code Review
                    </Button>
                    <Button 
                      variant="ghost" 
                      className="w-1/2 text-xs text-zinc-400 hover:text-white hover:bg-zinc-900/80"
                      disabled={project.status !== "completed"}
                    >
                      Enter Chat UI
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}