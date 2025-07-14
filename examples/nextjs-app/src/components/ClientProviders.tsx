"use client";

import { ThemeProvider } from "./ThemeProvider";
import { CopilotKit } from "@copilotkit/react-core";

interface ClientProvidersProps {
  children: React.ReactNode;
}

export function ClientProviders({ children }: ClientProvidersProps) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <CopilotKit runtimeUrl="/api/copilotkit">
        {children}
      </CopilotKit>
    </ThemeProvider>
  );
}
