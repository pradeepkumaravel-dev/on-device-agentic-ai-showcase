export type Role = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface ChatRequest {
  session_id: string;
  messages: ChatMessage[];
}

export type ChatResponse = ChatMessage; // backend returns { role: 'assistant', content: string }

export interface AgentChatMessage extends ChatMessage {
  agent?: string;
  screenshot?: string | null;
}

export interface AgentChatResponse {
  role: 'assistant';
  content: string;
  agent: string;
  screenshot: string | null;
}

export interface UsageInfo {
  total_tokens: number;
  max_context_tokens: number;
  threshold_percent: number;
  percent_used: number;
  should_summarize: boolean;
}

export type GraphNode = 'supervisor' | 'chat' | 'desktop' | 'screen';

export interface NodeStartEvent {
  type: 'node_start';
  node: GraphNode;
}

export interface NodeEndEvent {
  type: 'node_end';
  node: GraphNode;
}

export interface TokenEvent {
  type: 'token';
  node: GraphNode;
  content: string;
}

export interface ThinkingEvent {
  type: 'thinking';
  node: GraphNode;
  content: string;
}

export interface DoneEvent {
  type: 'done';
  content: string;
  agent: string | null;
  screenshot: string | null;
  usage: UsageInfo;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
}

export type StreamEvent = NodeStartEvent | NodeEndEvent | TokenEvent | ThinkingEvent | DoneEvent | ErrorEvent;

export interface SummarizeResponse {
  summary: string;
  usage: UsageInfo;
}
