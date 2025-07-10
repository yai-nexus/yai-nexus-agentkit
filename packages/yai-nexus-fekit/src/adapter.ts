import { ServiceAdapter } from "@copilotkit/runtime";
import { AgUiClient } from "@ag-ui/client";
import { AgUiMessage, AgUiResponse, AgUiEvent } from "@ag-ui/proto";

export interface YaiNexusAdapterConfig {
  backendUrl: string;
}

export class YaiNexusAdapter implements ServiceAdapter {
  private backendUrl: string;
  private client: AgUiClient;

  constructor(config: YaiNexusAdapterConfig) {
    this.backendUrl = config.backendUrl;
    this.client = new AgUiClient({
      baseUrl: this.backendUrl,
    });
  }

  async process(request: any): Promise<any> {
    try {
      // Convert CopilotKit request to ag-ui-protocol format
      const agUiMessage = this.convertCopilotToAgUi(request);
      
      // Send request to Python backend
      const response = await this.client.sendMessage(agUiMessage);
      
      // Convert ag-ui-protocol response back to CopilotKit format
      const copilotResponse = this.convertAgUiToCopilot(response);
      
      return copilotResponse;
    } catch (error) {
      console.error('YaiNexusAdapter process error:', error);
      throw error;
    }
  }

  async *stream(request: any): AsyncIterable<any> {
    try {
      // Convert CopilotKit request to ag-ui-protocol format
      const agUiMessage = this.convertCopilotToAgUi(request);
      
      // Get streaming response from Python backend
      const streamingResponse = await this.client.streamMessage(agUiMessage);
      
      // Process each chunk from the stream
      for await (const chunk of streamingResponse) {
        const copilotChunk = this.convertAgUiChunkToCopilot(chunk);
        if (copilotChunk) {
          yield copilotChunk;
        }
      }
    } catch (error) {
      console.error('YaiNexusAdapter stream error:', error);
      throw error;
    }
  }

  /**
   * Convert CopilotKit request format to ag-ui-protocol format
   */
  private convertCopilotToAgUi(copilotRequest: any): AgUiMessage {
    // Extract messages from CopilotKit request
    const messages = copilotRequest.messages || [];
    
    // Convert to ag-ui format
    const agUiMessage: AgUiMessage = {
      id: copilotRequest.id || this.generateId(),
      content: this.extractContent(messages),
      metadata: {
        timestamp: Date.now(),
        source: 'copilotkit',
        userId: copilotRequest.userId || 'anonymous',
      },
    };

    return agUiMessage;
  }

  /**
   * Convert ag-ui-protocol response to CopilotKit format
   */
  private convertAgUiToCopilot(agUiResponse: AgUiResponse): any {
    return {
      id: agUiResponse.id,
      content: agUiResponse.content,
      role: 'assistant',
      metadata: agUiResponse.metadata,
    };
  }

  /**
   * Convert ag-ui-protocol streaming chunk to CopilotKit format
   */
  private convertAgUiChunkToCopilot(agUiChunk: AgUiEvent): any {
    switch (agUiChunk.type) {
      case 'text_chunk':
        return {
          type: 'text',
          content: agUiChunk.data.text,
        };
      
      case 'tool_call':
        return {
          type: 'tool_call',
          name: agUiChunk.data.name,
          arguments: agUiChunk.data.arguments,
        };
      
      case 'tool_result':
        return {
          type: 'tool_result',
          result: agUiChunk.data.result,
        };
      
      case 'error':
        return {
          type: 'error',
          error: agUiChunk.data.error,
        };
      
      default:
        // Skip unknown chunk types
        return null;
    }
  }

  /**
   * Extract content from CopilotKit messages
   */
  private extractContent(messages: any[]): string {
    if (!messages || messages.length === 0) {
      return '';
    }
    
    // Get the last user message
    const lastMessage = messages[messages.length - 1];
    return lastMessage.content || '';
  }

  /**
   * Generate a unique ID for messages
   */
  private generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}