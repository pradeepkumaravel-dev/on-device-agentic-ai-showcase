interface ThinkingDrawerProps {
    open: boolean;
    content: string;
    onClose: () => void;
}

const ThinkingDrawer = ({ open, content, onClose }: ThinkingDrawerProps) => {
    return (
        <div className={`thinking-drawer ${open ? 'thinking-drawer--open' : ''}`}>
            <div className="thinking-drawer-header">
                <span>Reasoning</span>
                <button className="thinking-drawer-close" onClick={onClose} aria-label="Close">✕</button>
            </div>
            <div className="thinking-drawer-body">
                <pre className="thinking-drawer-text">{content}</pre>
            </div>
        </div>
    );
};

export default ThinkingDrawer;
