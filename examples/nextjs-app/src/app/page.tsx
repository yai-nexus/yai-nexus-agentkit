"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import { YaiNexusPersistenceProvider } from "@yai-nexus/fekit/client";
import { ThemeToggle } from "../components/ThemeToggle";

export default function Home() {
  const userId = "demo_user_12345";
  const conversationId = "default-chat";

  return (
    <div className="flex flex-col h-screen bg-gray-100 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 shadow-md z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold text-gray-800 dark:text-white">
              YAI Nexus FeKit Demo
            </h1>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 flex flex-col overflow-hidden">
        <YaiNexusPersistenceProvider
          userId={userId}
          conversationId={conversationId}
        >
          <CopilotChat
            labels={{
              title: "AI Assistant Chat",
              initial:
                "Hello! I'm your AI assistant. How can I help you today?",
            }}
            instructions="You are a helpful AI assistant integrated with the YAI Nexus AgentKit backend."
            className="copilot-chat flex-1"
          />
        </YaiNexusPersistenceProvider>
      </main>
    </div>
  );
}