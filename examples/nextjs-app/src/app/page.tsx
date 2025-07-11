"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { YaiNexusPersistenceProvider } from "@yai-nexus/fekit/client";

export default function Home() {
  const userId = "demo_user_12345";
  const conversationId = "default-chat";

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            YAI Nexus FeKit Demo
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            Demonstrating CopilotKit integration with yai-nexus-agentkit Python backend
          </p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg h-[600px] flex flex-col">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              AI Assistant Chat
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Chat messages are automatically persisted locally
            </p>
          </div>
          
          <div className="flex-1 overflow-hidden">
            <CopilotKit url="/api/copilotkit">
              <YaiNexusPersistenceProvider
                userId={userId}
                conversationId={conversationId}
              >
                <CopilotChat 
                  labels={{
                    title: "YAI Nexus Assistant",
                    initial: "Hello! I'm your AI assistant. How can I help you today?",
                  }}
                />
              </YaiNexusPersistenceProvider>
            </CopilotKit>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Features
            </h3>
            <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
              <li>• CopilotKit frontend integration</li>
              <li>• yai-nexus-agentkit Python backend connection</li>
              <li>• Automatic local chat persistence</li>
              <li>• Real-time streaming responses</li>
              <li>• IndexedDB storage with offline support</li>
            </ul>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Backend Status
            </h3>
            <div className="text-sm text-gray-600 dark:text-gray-300">
              <p>Backend URL: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">
                {process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000/invoke"}
              </code></p>
              <p className="mt-1">Make sure your Python backend is running to test the integration.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}