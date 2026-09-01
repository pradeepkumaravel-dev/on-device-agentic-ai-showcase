import type { GraphNode } from "../types/chat";

interface GraphTreeProps {
    activeNode: GraphNode | null;
    completedNodes: Set<GraphNode>;
}

const LEAVES: { node: GraphNode; label: string }[] = [
    { node: "chat", label: "Chat" },
    { node: "desktop", label: "Desktop" },
    { node: "screen", label: "Screen" },
];

function nodeStatus(node: GraphNode, activeNode: GraphNode | null, completedNodes: Set<GraphNode>) {
    if (activeNode === node) return "active";
    if (completedNodes.has(node)) return "done";
    return "idle";
}

function NodePill({ label, status }: { label: string; status: string }) {
    return (
        <div className={`tree-node tree-node--${status}`}>
            {status === "done" && <span className="tree-node-check">✓</span>}
            {status === "active" && <span className="tree-node-spinner" />}
            <span>{label}</span>
        </div>
    );
}

const GraphTree = ({ activeNode, completedNodes }: GraphTreeProps) => {
    return (
        <div className="graph-tree">
            <NodePill label="Supervisor" status={nodeStatus("supervisor", activeNode, completedNodes)} />
            <svg className="tree-connectors" viewBox="0 0 300 40" preserveAspectRatio="none">
                <path d="M150,0 L150,16 M150,16 L50,16 L50,40 M150,16 L150,40 M150,16 L250,16 L250,40" />
            </svg>
            <div className="tree-leaves">
                {LEAVES.map(({ node, label }) => (
                    <NodePill key={node} label={label} status={nodeStatus(node, activeNode, completedNodes)} />
                ))}
            </div>
        </div>
    );
};

export default GraphTree;
