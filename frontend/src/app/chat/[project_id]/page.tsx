"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
}

interface PageProps {
  params: Promise<{ project_id: string }>;
}

// ============================================================================
// CHAT-OPTIMIZED MARKDOWN & TERMINAL RENDERER
// ============================================================================
function CodeTerminal({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-4 rounded-xl border border-zinc-800 bg-zinc-950 overflow-hidden font-mono text-[11px] sm:text-xs shadow-2xl max-w-full">
      {/* Terminal Title Bar */}
      <div className="flex items-center justify-between bg-zinc-900/60 px-4 py-2 border-b border-zinc-900 select-none">
        <div className="flex items-center space-x-1.5">
          <div className="h-2.5 w-2.5 rounded-full bg-red-500/20 border border-red-500/30" />
          <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/30" />
          <div className="h-2.5 w-2.5 rounded-full bg-green-500/20 border border-green-500/30" />
          <span className="text-zinc-500 text-[9px] ml-2 uppercase tracking-widest">{language || "code"}</span>
        </div>
        <button
          onClick={handleCopy}
          className="text-zinc-500 hover:text-white transition-colors border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 px-2 py-0.5 rounded text-[9px]"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      {/* Code Area */}
      <pre className="p-4 overflow-x-auto text-zinc-300 leading-relaxed max-h-[350px]">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function ChatMessageRenderer({ rawText }: { rawText: string }) {
  if (!rawText) return null;

  // Split into code block chunks and text chunks
  const parts = rawText.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-4 font-sans text-sm text-zinc-200 leading-relaxed max-w-full">
      {parts.map((part, index) => {
        // Render Code Block Terminal
        if (part.startsWith("```")) {
          const match = part.match(/```(\w*)\n([\s\S]*?)```/);
          const lang = match ? match[1] : "";
          const code = match ? match[2].trim() : part.slice(3, -3).trim();
          return <CodeTerminal key={index} code={code} language={lang} />;
        }

        // Render Standard Text Chunks
        const lines = part.split("\n");
        return (
          <div key={index} className="space-y-3">
            {lines.map((line, lIdx) => {
              const trimmed = line.trim();
              if (!trimmed) return null;

              // Render Headings
              if (trimmed.startsWith("### ")) {
                return (
                  <h3 key={lIdx} className="text-sm font-semibold text-white tracking-wide mt-4 mb-1 flex items-center space-x-1.5">
                    <span className="text-indigo-400">◆</span>
                    <span>{trimmed.slice(4)}</span>
                  </h3>
                );
              }

              if (trimmed.startsWith("## ")) {
                return (
                  <h2 key={lIdx} className="text-sm font-bold text-white tracking-wide mt-5 mb-1.5 border-b border-zinc-900 pb-1">
                    {trimmed.slice(3)}
                  </h2>
                );
              }

              // Render Bullets
              if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
                const cleanLine = trimmed.slice(2);
                const inlineParts = cleanLine.split(/(\*\*.*?\*\*)/g);

                return (
                  <ul key={lIdx} className="list-none pl-3 space-y-1">
                    <li className="text-zinc-300 text-sm leading-relaxed flex items-start">
                      <span className="text-indigo-500 mr-2 mt-2 text-[6px]">●</span>
                      <span>
                        {inlineParts.map((inlinePart, ipIdx) => {
                          if (inlinePart.startsWith("**") && inlinePart.endsWith("**")) {
                            return <strong key={ipIdx} className="font-semibold text-white">{inlinePart.slice(2, -2)}</strong>;
                          }
                          return inlinePart;
                        })}
                      </span>
                    </li>
                  </ul>
                );
              }

              // Paragraphs
              const inlineParts = trimmed.split(/(\*\*.*?\*\*)/g);
              return (
                <p key={lIdx} className="text-zinc-300 text-sm leading-relaxed">
                  {inlineParts.map((inlinePart, ipIdx) => {
                    if (inlinePart.startsWith("**") && inlinePart.endsWith("**")) {
                      return <strong key={ipIdx} className="font-semibold text-white">{inlinePart.slice(2, -2)}</strong>;
                    }
                    return inlinePart;
                  })}
                </p>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

// ============================================================================
// MAIN CHAT INTERFACE COMPONENT
// ============================================================================
export default function ChatPage({ params }: PageProps) {
  const router = useRouter();
  const { project_id } = React.use(params);

  const [projectName, setProjectName] = useState("Loading project context...");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMsg, setInputMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  const messageEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    const loadProjectContext = async () => {
      try {
        const projects = await apiFetch<any[]>("/projects");
        const match = projects.find((p) => p.id === project_id);
        if (match) {
          setProjectName(match.name);
          
          // NEW: Fetch past conversation history from PostgreSQL
          const history = await apiFetch<Message[]>(`/chat/project/${project_id}`);
          setMessages(history);
        } else {
          router.push("/dashboard");
        }
      } catch (err) {
        console.error("Failed to load chat context", err);
        router.push("/dashboard");
      } finally {
        setIsInitializing(false);
      }
    };

    loadProjectContext();
  }, [project_id]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: inputMsg };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputMsg;
    setInputMsg("");
    setIsLoading(true);

    try {
      const data = await apiFetch<{ answer: string; retrieved_sources: any[] }>("/chat/query", {
        method: "POST",
        body: JSON.stringify({
          project_id: project_id,
          question: currentInput,
        }),
      });

      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer,
        sources: data.retrieved_sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        role: "assistant",
        content: `❌ System error: Unable to contact the query pipeline. ${err.message}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (isInitializing) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black text-zinc-500 font-mono text-sm">
        Initializing secure code-intelligence context...
      </div>
    );
  }

  return (
    <div className="relative flex flex-col h-screen bg-black text-white font-sans overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(99,102,241,0.03),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      {/* Dynamic Header */}
      <header className="relative z-10 border-b border-zinc-800/80 bg-zinc-950/40 backdrop-blur-md px-6 py-4 flex items-center justify-between select-none">
        <div className="flex items-center space-x-4">
          <Link href="/dashboard">
            <Button variant="outline" className="text-xs border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-900">
              ← Dashboard
            </Button>
          </Link>
          <div className="h-4 w-px bg-zinc-800" />
          <div>
            <h1 className="font-semibold text-base text-white tracking-tight">{projectName}</h1>
            <p className="text-xs text-zinc-500 font-mono">Index ID: {project_id}</p>
          </div>
        </div>
      </header>

      {/* Scrollable Message History Area */}
      <main className="relative z-10 flex-1 overflow-y-auto px-6 py-8 space-y-6">
        {messages.length === 0 ? (
          <div className="max-w-2xl mx-auto text-center py-20 space-y-4 select-none">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              💬
            </div>
            <h2 className="text-xl font-semibold text-white">Ask your Codebase Anything</h2>
            <p className="text-zinc-500 text-sm max-w-md mx-auto">
              DevPilot AI will analyze your workspace index, retrieve the matching code blocks, and write a grounded technical response.
            </p>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((msg, index) => (
              <div key={index} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div className="text-xs text-zinc-600 mb-1 font-mono uppercase tracking-wider px-2 select-none">
                  {msg.role}
                </div>
                {/* Message Bubble Container */}
                <div className={`max-w-3xl rounded-2xl px-5 py-4 text-sm leading-relaxed border ${
                  msg.role === "user"
                    ? "bg-zinc-900 border-zinc-800 text-zinc-100 rounded-tr-none whitespace-pre-wrap font-sans text-zinc-200"
                    : "bg-zinc-950/60 border-zinc-800/80 text-zinc-100 rounded-tl-none backdrop-blur-sm"
                }`}>
                  {msg.role === "user" ? (
                    msg.content
                  ) : (
                    /* Render beautifully formatted markdown and code blocks */
                    <ChatMessageRenderer rawText={msg.content} />
                  )}
                </div>

                {/* Source Attribution Cards (Display only on AI replies containing retrieved files) */}
                {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                  <div className="max-w-3xl w-full mt-3 space-y-2 px-1">
                    <span className="text-xs font-mono text-zinc-500 select-none">Retrieved Context Sources:</span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {msg.sources.map((source, sIdx) => {
                        const meta = source.metadata;
                        return (
                          <Card key={sIdx} className="border-zinc-900 bg-zinc-950/20 hover:bg-zinc-950/50 hover:border-zinc-800 transition-colors p-3 flex flex-col justify-between">
                            <div>
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-xs font-mono text-indigo-400 font-semibold truncate max-w-[150px]">
                                  {meta.file_path.split("/").pop()}
                                </span>
                                <span className="text-[10px] font-mono text-zinc-600">
                                  Lines: {meta.start_line}-{meta.end_line}
                                </span>
                              </div>
                              <p className="text-[11px] text-zinc-500 font-mono truncate">{meta.file_path}</p>
                            </div>
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex flex-col items-start">
                <div className="text-xs text-zinc-600 mb-1 font-mono uppercase tracking-wider px-2 select-none">
                  assistant
                </div>
                <div className="rounded-2xl rounded-tl-none px-5 py-4 border border-zinc-800/80 bg-zinc-950/60 backdrop-blur-sm text-sm text-zinc-400 font-mono animate-pulse">
                  Analyzing code vectors and generating response...
                </div>
              </div>
            )}
            <div ref={messageEndRef} />
          </div>
        )}
      </main>

      {/* Floating Query Input Box */}
      <footer className="relative z-10 border-t border-zinc-800/80 bg-zinc-950/60 backdrop-blur-md px-6 py-6">
        <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto flex items-center space-x-3">
          <Input
            type="text"
            placeholder="Search files or ask, e.g., 'How are passwords hashed and stored?'"
            value={inputMsg}
            onChange={(e) => setInputMsg(e.target.value)}
            disabled={isLoading}
            className="flex-1 border-zinc-800 bg-zinc-900/40 text-white placeholder-zinc-600 focus:border-indigo-500 focus:ring-indigo-500/20 h-11"
          />
          <Button 
            type="submit" 
            disabled={isLoading || !inputMsg.trim()}
            className="h-11 bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white shadow-lg shadow-indigo-500/10 px-6 font-semibold transition-all duration-200"
          >
            Ask AI
          </Button>
        </form>
      </footer>
    </div>
  );
}