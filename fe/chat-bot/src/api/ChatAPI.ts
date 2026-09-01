import { apiClient } from "./Client";


import type { AgentChatResponse, ChatRequest, ChatResponse, StreamEvent, SummarizeResponse } from "../types/chat";

export async function sendMessage(payload: ChatRequest) : Promise<ChatResponse> {
    const {data} = await apiClient.post<ChatResponse>('/chat/invoke-model',payload);
    return data;
}

export async function sendAgentMessage(payload: ChatRequest): Promise<AgentChatResponse> {
    const { data } = await apiClient.post<AgentChatResponse>('/chat/desktop-agent', payload);
    return data;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// EventSource can't send a POST body, so the SSE stream is read manually via
// fetch + a ReadableStream reader instead.
export async function streamAgentMessage(
    payload: ChatRequest,
    onEvent: (event: StreamEvent) => void,
    signal?: AbortSignal,
): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/chat/desktop-agent/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal,
    });
    if (!response.body) throw new Error('No response body for stream');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const messages = buffer.split('\n\n');
        buffer = messages.pop() ?? '';

        for (const message of messages) {
            const line = message.split('\n').find((l) => l.startsWith('data: '));
            if (!line) continue;
            const jsonStr = line.slice('data: '.length);
            onEvent(JSON.parse(jsonStr) as StreamEvent);
        }
    }
}

export async function summarize(payload: ChatRequest): Promise<SummarizeResponse> {
    const { data } = await apiClient.post<SummarizeResponse>('/chat/summarize', payload);
    return data;
}