import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { AgentChatMessage } from "../types/chat";

interface MessageBubbleProps {
    message: AgentChatMessage;
}

const MessageBubble = ({ message }: MessageBubbleProps) => {
    return (
        <div className={message.role === "assistant" ? "chat-left" : "chat-right"}>
            {message.role === "assistant" && message.agent && (
                <span className="agent-badge">{message.agent}</span>
            )}
            <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
            {message.screenshot && (
                <img
                    className="chat-screenshot-thumb"
                    src={`data:image/png;base64,${message.screenshot}`}
                    alt="screenshot"
                />
            )}
        </div>
    );
};

// Only the actively-streaming message's `message` prop reference changes
// (see ChatBot's append logic - all other message objects keep their prior
// reference), so memo lets every settled message skip re-rendering, and
// re-parsing its markdown, on each token of the current one.
export default memo(MessageBubble);
