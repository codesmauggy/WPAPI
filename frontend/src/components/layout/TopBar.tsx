import {
  Search,
  Bell,
  UserCircle,
} from "lucide-react";

interface TopBarProps {
  title: string;
}

export default function TopBar({ title }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="topbar-title">
        <h1>{title}</h1>
      </div>

      <div className="topbar-actions">
        <button className="icon-button" type="button" aria-label="Search">
          <Search size={20} />
        </button>

        <button className="icon-button" type="button" aria-label="Notifications">
          <Bell size={20} />
        </button>

        <button className="profile-button" type="button" aria-label="Profile">
          <UserCircle size={28} />
        </button>
      </div>
    </header>
  );
}