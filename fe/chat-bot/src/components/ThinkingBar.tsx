interface ThinkingBarProps {
    onClick: () => void;
}

const ThinkingBar = ({ onClick }: ThinkingBarProps) => {
    return (
        <button className="thinking-bar" onClick={onClick}>
            <span className="thinking-bar-dot" />
            <span className="thinking-bar-dot" />
            <span className="thinking-bar-dot" />
            <span className="thinking-bar-label">Thinking… tap to view reasoning</span>
        </button>
    );
};

export default ThinkingBar;
