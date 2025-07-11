import { createYaiNexusHandler } from "@yai-nexus/fekit/server";

const handler = createYaiNexusHandler({
  backendUrl: process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000/invoke",
  logging: {
    enabled: true,
    progressive: true,
  },
});