import type { ReactNode } from "react";

interface RightPanelProps {
  children?: ReactNode;
  title?: string;
}

export default function RightPanel({
  children,
  title = "Business Operations",
}: RightPanelProps) {
  return (
    <aside className="right-panel">
      <div className="right-panel-header">
        <h2>{title}</h2>
      </div>

      <div className="right-panel-content">
        {children}
      </div>
    </aside>
  );
}