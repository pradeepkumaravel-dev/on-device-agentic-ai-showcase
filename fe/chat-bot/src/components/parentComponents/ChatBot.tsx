import { useRef, useState, useEffect } from "react";
import type { AgentChatMessage, ChatMessage, GraphNode, StreamEvent, UsageInfo, Session } from "../../types/chat";
import { streamAgentMessage, summarize, getSessions, getChatHistory, deleteSession } from "../../api/ChatAPI";
import GraphTree from "../GraphTree";
import MessageBubble from "../MessageBubble";
import TokenUsageBar from "../TokenUsageBar";
import ThinkingBar from "../ThinkingBar";
import ThinkingDrawer from "../ThinkingDrawer";
import { SessionSidebar } from "../SessionSidebar";

const ChatBot = () => {
    const [sessionId, setSessionId] = useState<string>(crypto.randomUUID());
    const [sessions, setSessions] = useState<Session[]>([]);

    // displayMessages: full history, always rendered.
    // contextMessages: what's actually sent to the model each turn - starts
    // equal to displayMessages, replaced with a single summary message after
    // Summarize while displayMessages keeps the full scrollback untouched.
    const [displayMessages, setDisplayMessages] = useState<AgentChatMessage[]>([
        { role: "assistant", content: "Howdy mate" },
    ]);
    const [contextMessages, setContextMessages] = useState<ChatMessage[]>([
        { role: "assistant", content: "Howdy mate" },
    ]);

    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSummarizing, setIsSummarizing] = useState(false);
    const [activeNode, setActiveNode] = useState<GraphNode | null>(null);
    const [completedNodes, setCompletedNodes] = useState<Set<GraphNode>>(new Set());
    const [usage, setUsage] = useState<UsageInfo | null>(null);
    const [contextSummary, setContextSummary] = useState<string | null>(null);

    // Transient, current-turn-only reasoning state - not attached to message
    // history, discarded on the next send.
    const [isThinking, setIsThinking] = useState(false);
    const [currentThinkingText, setCurrentThinkingText] = useState('');
    const [thinkingDrawerOpen, setThinkingDrawerOpen] = useState(false);

    useEffect(() => {
        const fetchSessions = async () => {
            try {
                const data = await getSessions();
                setSessions(data);
            } catch (err) {
                console.error("Failed to load sessions", err);
            }
        };
        fetchSessions();
    }, []);

    const handleSelectSession = async (id: string) => {
        if (id === sessionId) return;
        setSessionId(id);
        try {
            const history = await getChatHistory(id);
            setDisplayMessages(history.length ? history : [{ role: "assistant", content: "Howdy mate" }]);
            setContextMessages(history.length ? history : [{ role: "assistant", content: "Howdy mate" }]);
        } catch(err) {
            console.error("Failed to load history", err);
        }
    };

    const handleNewChat = () => {
        setSessionId(crypto.randomUUID());
        setDisplayMessages([{ role: "assistant", content: "Howdy mate" }]);
        setContextMessages([{ role: "assistant", content: "Howdy mate" }]);
    };

    const handleDeleteSession = async (id: string) => {
        try {
            await deleteSession(id);
            setSessions(prev => prev.filter(s => s.id !== id));
            if (id === sessionId) {
                handleNewChat();
            }
        } catch (err) {
            console.error("Failed to delete session", err);
        }
    };

    // Token deltas are buffered and flushed once per animation frame instead
    // of one setState per SSE token - qwen3's reasoning mode alone can emit
    // hundreds of stream chunks per reply, and without batching each one
    // triggers a full re-render of the message list.
    const pendingTokenRef = useRef('');
    const flushScheduledRef = useRef(false);

    const flushPendingTokens = () => {
        flushScheduledRef.current = false;
        if (!pendingTokenRef.current) return;
        const chunk = pendingTokenRef.current;
        pendingTokenRef.current = '';
        setDisplayMessages((prev) => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            updated[lastIdx] = { ...updated[lastIdx], content: updated[lastIdx].content + chunk };
            return updated;
        });
    };

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: ChatMessage = { role: 'user', content: input };
        const newContext = [...contextMessages, userMessage];

        setDisplayMessages((prev) => [...prev, userMessage, { role: 'assistant', content: '' }]);
        setContextMessages(newContext);
        setInput('');
        setIsLoading(true);
        setActiveNode(null);
        setCompletedNodes(new Set());
        setIsThinking(false);
        setCurrentThinkingText('');
        setThinkingDrawerOpen(false);
        pendingTokenRef.current = '';

        const appendToLastMessage = (patch: Partial<AgentChatMessage>) => {
            setDisplayMessages((prev) => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                updated[lastIdx] = { ...updated[lastIdx], ...patch };
                return updated;
            });
        };

        const onEvent = (event: StreamEvent) => {
            switch (event.type) {
                case 'node_start':
                    setActiveNode(event.node);
                    break;
                case 'node_end':
                    setCompletedNodes((prev) => new Set(prev).add(event.node));
                    setActiveNode((current) => (current === event.node ? null : current));
                    break;
                case 'thinking':
                    setCurrentThinkingText((prev) => prev + event.content);
                    setIsThinking(true);
                    break;
                case 'token':
                    setIsThinking(false);
                    pendingTokenRef.current += event.content;
                    if (!flushScheduledRef.current) {
                        flushScheduledRef.current = true;
                        requestAnimationFrame(flushPendingTokens);
                    }
                    break;
                case 'done':
                    // event.content is the authoritative full text - discard
                    // any not-yet-flushed buffer so a stale rAF flush can't
                    // land after this and duplicate/garble the final content.
                    pendingTokenRef.current = '';
                    setIsThinking(false);
                    setThinkingDrawerOpen(false);
                    appendToLastMessage({
                        content: event.content,
                        agent: event.agent ?? undefined,
                        screenshot: event.screenshot,
                    });
                    setContextMessages((prev) => [...prev, { role: 'assistant', content: event.content }]);
                    setUsage(event.usage);
                    break;
                case 'error':
                    pendingTokenRef.current = '';
                    appendToLastMessage({ content: `Error: ${event.message}` });
                    break;
                case 'session_title':
                    setSessions(prev => {
                        const exists = prev.find(s => s.id === sessionId);
                        if (exists) {
                            return prev.map(s => s.id === sessionId ? { ...s, title: event.title } : s);
                        } else {
                            return [{ id: sessionId, title: event.title, created_at: '', updated_at: '' }, ...prev];
                        }
                    });
                    break;
            }
        };

        try {
            await streamAgentMessage({ session_id: sessionId, messages: newContext }, onEvent);
        } catch (err) {
            pendingTokenRef.current = '';
            appendToLastMessage({ content: `Error: ${(err as Error).message}` });
        } finally {
            setIsLoading(false);
            setActiveNode(null);
            setIsThinking(false);
        }
    };

    const handleSummarize = async () => {
        if (isSummarizing) return;
        setIsSummarizing(true);
        try {
            const result = await summarize({ session_id: sessionId, messages: contextMessages });
            setContextMessages([
                { role: 'system', content: `Summary of earlier conversation: ${result.summary}` },
            ]);
            setContextSummary(result.summary);
            setUsage(result.usage);
        } finally {
            setIsSummarizing(false);
        }
    };

    return (
        <div className="page-container">
            <SessionSidebar 
                sessions={sessions}
                activeSessionId={sessionId}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
                onDeleteSession={handleDeleteSession}
            />
            <aside className="side-panel">
                <div className="side-panel-section">
                    <h2 className="side-panel-title">Graph execution</h2>
                    <GraphTree activeNode={activeNode} completedNodes={completedNodes} />
                </div>
                <div className="side-panel-section">
                    <h2 className="side-panel-title">Token budget</h2>
                    <TokenUsageBar usage={usage} onSummarize={handleSummarize} isSummarizing={isSummarizing} />
                </div>
                <div className="side-panel-section">
                    <h2 className="side-panel-title">Context</h2>
                    {contextSummary ? (
                        <p className="context-summary-text">{contextSummary}</p>
                    ) : (
                        <p className="context-empty">Full conversation in context — no summary yet.</p>
                    )}
                </div>
            </aside>

            <div className="main-panel">
                <div className="chat-bot-container">
                    {displayMessages.map((ele, idx) => (
                        <MessageBubble key={idx} message={ele} />
                    ))}
                    {isLoading && !activeNode && <div className="chat-left chat-loading">…</div>}
                </div>
                {isThinking ? (
                    <div className="text-area">
                        <ThinkingBar onClick={() => setThinkingDrawerOpen(true)} />
                    </div>
                ) : (
                    <div className="text-area">
                        <div className="text-box-container">
                            <input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') handleSend(); }}
                                disabled={isLoading}
                                className="text-box"
                            ></input>
                            <button className="submit-button" onClick={() => handleSend()} disabled={isLoading}>Send</button>
                        </div>
                    </div>
                )}
                <ThinkingDrawer
                    open={thinkingDrawerOpen}
                    content={currentThinkingText}
                    onClose={() => setThinkingDrawerOpen(false)}
                />
            </div>
        </div>
    )
}


export default ChatBot;
