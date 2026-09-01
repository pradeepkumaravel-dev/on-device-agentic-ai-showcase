import type { UsageInfo } from "../types/chat";

interface TokenUsageBarProps {
    usage: UsageInfo | null;
    onSummarize: () => void;
    isSummarizing: boolean;
}

function barColor(percentUsed: number, thresholdPercent: number): string {
    if (percentUsed >= thresholdPercent) return "var(--danger)";
    if (percentUsed >= thresholdPercent * 0.66) return "var(--warning)";
    return "var(--accent)";
}

const TokenUsageBar = ({ usage, onSummarize, isSummarizing }: TokenUsageBarProps) => {
    if (!usage) return null;

    const percent = Math.min(usage.percent_used, 100);

    return (
        <div className="token-usage">
            <div className="token-usage-label">
                <span>Context usage</span>
                <span>{usage.total_tokens} / {usage.max_context_tokens} tokens</span>
            </div>
            <div className="token-usage-track">
                <div
                    className="token-usage-fill"
                    style={{ width: `${percent}%`, backgroundColor: barColor(usage.percent_used, usage.threshold_percent) }}
                />
            </div>
            {usage.should_summarize && (
                <button className="summarize-button" onClick={onSummarize} disabled={isSummarizing}>
                    {isSummarizing ? "Summarizing…" : "Summarize conversation"}
                </button>
            )}
        </div>
    );
};

export default TokenUsageBar;
