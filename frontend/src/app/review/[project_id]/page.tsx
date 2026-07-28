"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface PageProps {
  params: Promise<{ project_id: string }>;
}

export default function ReviewPage({ params }: PageProps) {
  const router = useRouter();
  const { project_id } = React.use(params);

  const [projectName, setProjectName] = useState("Loading project...");
  const [activeTab, setActiveTab] = useState<"review" | "docs">("review");
  const [isInitializing, setIsInitializing] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Store generated markdown reports locally in state
  const [reviewReport, setReviewReport] = useState("");
  const [readmeContent, setReadmeContent] = useState("");

  useEffect(() => {
    const loadProjectContext = async () => {
      try {
        const projects = await apiFetch<any[]>("/projects");
        const match = projects.find((p) => p.id === project_id);
        if (match) {
          setProjectName(match.name);
        } else {
          router.push("/dashboard");
        }
      } catch (err) {
        router.push("/dashboard");
      } finally {
        setIsInitializing(false);
      }
    };

    loadProjectContext();
  }, [project_id]);

  // Call the backend Automated Code Review endpoint
  const triggerCodeReview = async () => {
    setIsLoading(true);
    setErrorMsg("");
    try {
      const data = await apiFetch<{ review_report: string }>(`/review/project/${project_id}`, {
        method: "POST",
      });
      setReviewReport(data.review_report);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to complete security audit. Rate limit may be active.");
    } finally {
      setIsLoading(false);
    }
  };

  // Call the backend Autonomous Documentation Generator
  const triggerDocGeneration = async () => {
    setIsLoading(true);
    setErrorMsg("");
    try {
      const data = await apiFetch<{ readme_content: string }>(`/review/project/${project_id}/docs`, {
        method: "POST",
      });
      setReadmeContent(data.readme_content);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate README. Rate limit may be active.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isInitializing) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black text-zinc-500 font-mono text-sm">
        Initializing secure audit workspace...
      </div>
    );
  }

  const activeContent = activeTab === "review" ? reviewReport : readmeContent;

  return (
    <div className="relative min-h-screen bg-black text-white overflow-hidden font-sans pb-16">
      {/* Background radial overlays */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(99,102,241,0.03),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      {/* Global Header */}
      <header className="relative z-10 border-b border-zinc-800/80 bg-zinc-950/40 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/dashboard">
            <Button variant="outline" className="text-xs border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-900">
              ← Dashboard
            </Button>
          </Link>
          <div className="h-4 w-px bg-zinc-800" />
          <div>
            <h1 className="font-semibold text-base text-white tracking-tight">{projectName} — Auditing Suite</h1>
            <p className="text-xs text-zinc-500 font-mono">Workspace ID: {project_id}</p>
          </div>
        </div>
      </header>

      {/* Workspace Dashboard */}
      <main className="relative z-10 max-w-5xl mx-auto px-6 py-8 space-y-8">
        
        {/* Navigation Tabs and Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
          <div className="flex space-x-2 bg-zinc-900/60 p-1 rounded-lg border border-zinc-800/50 max-w-fit">
            <button
              onClick={() => { setActiveTab("review"); setErrorMsg(""); }}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === "review"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              AI Code Review
            </button>
            <button
              onClick={() => { setActiveTab("docs"); setErrorMsg(""); }}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === "docs"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              README.md Generator
            </button>
          </div>

          <Button
            onClick={activeTab === "review" ? triggerCodeReview : triggerDocGeneration}
            disabled={isLoading}
            className="bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white shadow-lg shadow-indigo-500/10 font-semibold text-sm h-10 px-6 transition-all duration-200"
          >
            {isLoading 
              ? "Running AI Analysis..." 
              : activeTab === "review" 
              ? "Run Code Review Audit" 
              : "Generate README.md"
            }
          </Button>
        </div>

        {errorMsg && (
          <div className="rounded-lg bg-red-950/30 p-4 text-sm text-red-400 border border-red-900/50 max-w-3xl mx-auto">
            {errorMsg}
          </div>
        )}

        {/* Dynamic Display Board */}
        <div className="max-w-4xl mx-auto">
          {!activeContent && !isLoading ? (
            <Card className="border-zinc-800/80 bg-zinc-950/20 py-20 text-center border-dashed">
              <CardContent className="space-y-4">
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/10 text-violet-400 border border-violet-500/20">
                  {activeTab === "review" ? "🚨" : "📝"}
                </div>
                <h3 className="text-lg font-semibold text-white">
                  {activeTab === "review" ? "Initiate Codebase Audit" : "Generate Production Documentation"}
                </h3>
                <p className="text-zinc-500 text-sm max-w-md mx-auto">
                  {activeTab === "review"
                    ? "Click the button above to run a staff-level security, logical, and performance evaluation on this codebase."
                    : "Autonomously generate a professional markdown README explaining the folder structure, technical stacks, and setup instructions."}
                </p>
              </CardContent>
            </Card>
          ) : isLoading ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-12 text-center text-zinc-400 font-mono animate-pulse">
              Parsing file structures, running neural semantic analyzers, and compiling report markdown...
            </div>
          ) : (
            /* Styled Long-Form Markdown Report Container */
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 backdrop-blur-md p-8 shadow-2xl leading-relaxed text-zinc-300 whitespace-pre-wrap font-sans text-sm selection:bg-indigo-500 selection:text-white">
              {activeContent}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}