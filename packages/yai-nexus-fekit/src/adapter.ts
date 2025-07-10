import { CopilotServiceAdapter } from "@copilotkit/runtime";
import { HttpAgent, Message, BaseEvent, EventType } from "@ag-ui/client";
import { Observable } from "rxjs";

export interface YaiNexusAdapterConfig {
  backendUrl: string;
}

export class YaiNexusAdapter implements CopilotServiceAdapter {
  private backendUrl: string;
  private agent: HttpAgent;

  constructor(config: YaiNexusAdapterConfig) {
    this.backendUrl = config.backendUrl;
    this.agent = new HttpAgent({
      url: this.backendUrl,
    });
  }

  async process(request: any): Promise<any> {
    try {
      // Convert CopilotKit request to ag-ui-protocol format
      const messages = this.convertCopilotToAgUi(request);
      
      // Prepare input for agent
      const agentInput = {
        threadId: request.threadId || this.generateId(),
        runId: request.runId || this.generateId(),
        messages,
        tools: [],
        context: [],
        state: null,
      };
      
      // Send request to Python backend and collect response
      const events$ = this.agent.run(agentInput);
      const response = await this.collectResponse(events$);
      
      return response;
    } catch (error) {
      console.error('YaiNexusAdapter process error:', error);
      throw error;
    }
  }

  async *stream(request: any): AsyncIterable<any> {
    try {
      // Convert CopilotKit request to ag-ui-protocol format
      const messages = this.convertCopilotToAgUi(request);
      
      // Prepare input for agent
      const agentInput = {
        threadId: request.threadId || this.generateId(),
        runId: request.runId || this.generateId(),
        messages,
        tools: [],
        context: [],
        state: null,
      };
      
      // Get streaming response from Python backend
      const events$ = this.agent.run(agentInput);
      
      // Convert observable to async generator
      yield* this.observableToAsyncGenerator(events$);
    } catch (error) {
      console.error('YaiNexusAdapter stream error:', error);
      throw error;
    }
  }

  /**
   * Convert CopilotKit request format to ag-ui-protocol format
   */
  private convertCopilotToAgUi(copilotRequest: any): Message[] {
    // Extract ALL messages from CopilotKit request (not just the last one)
    const copilotMessages = copilotRequest.messages || [];
    
    // Convert each message to ag-ui format
    const agUiMessages: Message[] = copilotMessages.map((msg: any) => ({
      id: msg.id || this.generateId(),
      role: msg.role,
      content: msg.content || '',
      name: msg.name,
    }));

    return agUiMessages;
  }

  /**
   * Convert ag-ui-protocol response to CopilotKit format
   */
  private convertAgUiToCopilot(agUiResponse: any): any {
    return {
      id: agUiResponse.id || this.generateId(),
      content: agUiResponse.content || '',
      role: 'assistant',
      metadata: agUiResponse.metadata || {},
    };
  }

  /**
   * Convert ag-ui-protocol streaming event to CopilotKit format
   */
  private convertAgUiChunkToCopilot(event: BaseEvent): any {
    // For now, return a simple text format
    // TODO: Properly handle different event types based on ag-ui protocol
    return {
      type: 'content',
      content: JSON.stringify(event),
    };
  }

  /**
   * Collect response from Observable stream
   */
  private async collectResponse(events$: Observable<BaseEvent>): Promise<any> {
    return new Promise((resolve, reject) => {
      let content = '';
      
      events$.subscribe({
        next: (event) => {
          // Accumulate text content from events
          if (event.type === EventType.TEXT_MESSAGE_CHUNK) {
            content += (event as any).text || '';
          }
        },
        error: reject,
        complete: () => {
          resolve({
            id: this.generateId(),
            content,
            role: 'assistant'
          });
        }
      });
    });
  }

  /**
   * Convert Observable to AsyncGenerator
   */
  private async *observableToAsyncGenerator(events$: Observable<BaseEvent>): AsyncIterable<any> {
    const events: BaseEvent[] = [];
    let completed = false;
    let error: any = null;

    events$.subscribe({
      next: (event) => events.push(event),
      error: (err) => { error = err; },
      complete: () => { completed = true; }
    });

    while (!completed && !error) {
      if (events.length > 0) {
        const event = events.shift()!;
        const chunk = this.convertAgUiChunkToCopilot(event);
        if (chunk) {
          yield chunk;
        }
      } else {
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    }

    if (error) {
      throw error;
    }

    // Process remaining events
    while (events.length > 0) {
      const event = events.shift()!;
      const chunk = this.convertAgUiChunkToCopilot(event);
      if (chunk) {
        yield chunk;
      }
    }
  }

  /**
   * Generate a unique ID for messages
   */
  private generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}