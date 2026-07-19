import { ModulePage } from "@/components/common/module-page";
import { AiAssistant } from "@/components/rag/ai-assistant";
import { Bot } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Assistant | CausalCast AI",
  description:
    "Ask grounded questions about indexed CausalCast AI project documents.",
};

export default function AiAssistantPage() {
  return (
    <ModulePage title="AI Assistant" icon={<Bot className="text-cyan-300" />}>
      <AiAssistant />
    </ModulePage>
  );
}
