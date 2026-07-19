"use client";

import { streamRagChat } from "@/lib/api";
import type { RagStreamEvent } from "@/types/rag";
import { Bot, Clipboard, RotateCcw, Send, UserRound } from "lucide-react";
import { FormEvent, useState } from "react";

interface Conversation {
  id: number;
  question: string;
  answer: string;
  sources: string[];
  pending: boolean;
}

const suggestions = [
  "What API endpoints are available?",
  "How is recursive forecasting implemented?",
  "Explain the model comparison metrics.",
];

export function AiAssistant() {
  const [question, setQuestion] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [error, setError] = useState<string | null>(null);

  const ask = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const submitted = question.trim();
    if (!submitted) return;

    const id = Date.now();
    setQuestion("");
    setError(null);
    setConversations((current) => [
      ...current,
      { id, question: submitted, answer: "", sources: [], pending: true },
    ]);

    const receive = (streamEvent: RagStreamEvent) => {
      setConversations((current) =>
        current.map((item) => {
          if (item.id !== id) return item;
          if (streamEvent.type === "token") {
            return { ...item, answer: item.answer + streamEvent.content };
          }
          if (streamEvent.type === "sources") {
            return { ...item, sources: streamEvent.sources };
          }
          return { ...item, pending: false };
        }),
      );
    };

    try {
      await streamRagChat({ question: submitted }, receive);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The assistant is unavailable.",
      );
      setConversations((current) =>
        current.map((item) =>
          item.id === id ? { ...item, pending: false } : item,
        ),
      );
    }
  };

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/60 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
        <div>
          <h3 className="font-semibold text-white">
            Project document assistant
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Answers are restricted to indexed project documents.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setConversations([]);
            setError(null);
          }}
          disabled={conversations.length === 0}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-300 transition hover:border-slate-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RotateCcw size={14} />
          Clear chat
        </button>
      </div>

      <div className="min-h-96 space-y-6 p-5" aria-live="polite">
        {conversations.length === 0 ? (
          <div className="grid min-h-80 place-items-center text-center">
            <div className="max-w-xl">
              <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl border border-cyan-500/25 bg-cyan-500/10 text-cyan-300">
                <Bot />
              </span>
              <h4 className="mt-5 text-lg font-semibold text-white">
                Ask about CausalCast AI
              </h4>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Search architecture, API, report, and model-comparison
                documentation. If the answer is not indexed, the assistant will
                say so.
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-2">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setQuestion(suggestion)}
                    className="rounded-full border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-300 hover:border-cyan-500/50 hover:text-cyan-200"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          conversations.map((conversation) => (
            <article key={conversation.id} className="space-y-3">
              <div className="ml-auto flex max-w-3xl items-start gap-3 rounded-2xl bg-blue-600/15 p-4">
                <UserRound
                  className="mt-0.5 shrink-0 text-blue-300"
                  size={18}
                />
                <p className="text-sm leading-6 text-slate-100">
                  {conversation.question}
                </p>
              </div>
              <div className="mr-auto max-w-3xl rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                <div className="flex items-start gap-3">
                  <Bot className="mt-0.5 shrink-0 text-cyan-300" size={18} />
                  <p className="min-h-6 text-sm leading-6 whitespace-pre-wrap text-slate-200">
                    {conversation.answer ||
                      (conversation.pending
                        ? "Searching project documents…"
                        : "")}
                  </p>
                </div>
                {conversation.sources.length > 0 && (
                  <div className="mt-4 border-t border-slate-800 pt-3">
                    <p className="text-xs font-medium text-slate-400">
                      Sources
                    </p>
                    <ul className="mt-2 flex flex-wrap gap-2">
                      {conversation.sources.map((source) => (
                        <li
                          key={source}
                          className="rounded-md border border-cyan-500/20 bg-cyan-500/10 px-2 py-1 font-mono text-xs text-cyan-200"
                        >
                          {source}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {conversation.answer && !conversation.pending && (
                  <button
                    type="button"
                    onClick={() =>
                      navigator.clipboard.writeText(conversation.answer)
                    }
                    aria-label="Copy response"
                    className="mt-3 inline-flex items-center gap-2 text-xs text-slate-400 hover:text-white"
                  >
                    <Clipboard size={13} /> Copy response
                  </button>
                )}
              </div>
            </article>
          ))
        )}
        {error && (
          <div
            role="alert"
            className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200"
          >
            {error}
          </div>
        )}
      </div>

      <form onSubmit={ask} className="border-t border-slate-800 p-4">
        <label htmlFor="rag-question" className="sr-only">
          Ask a question about the project
        </label>
        <div className="flex gap-3">
          <textarea
            id="rag-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            rows={2}
            maxLength={2000}
            placeholder="Ask about project documents…"
            className="min-w-0 flex-1 resize-none rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={
              !question.trim() || conversations.some((item) => item.pending)
            }
            className="inline-flex items-center gap-2 self-stretch rounded-xl bg-cyan-500 px-4 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send size={17} />
            <span className="hidden sm:inline">Ask</span>
          </button>
        </div>
      </form>
    </div>
  );
}
