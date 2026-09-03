import type { ReactNode } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import RightPanel from "./RightPanel";

interface AppShellProps {
  activeItem: string;
  title: string;
  onNavigate: (item: string) => void;
  children: ReactNode;
  rightPanel?: ReactNode;
}

export default function AppShell({
  activeItem,
  title,
  onNavigate,
  children,
  rightPanel,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <Sidebar
        activeItem={activeItem}
        onNavigate={onNavigate}
      />

      <main className="main-area">
        <TopBar title={title} />

        <div className="workspace">
          <section className="content-area">
            {children}
          </section>

          <RightPanel>
            {rightPanel}
          </RightPanel>
        </div>
      </main>
    </div>
  );
}