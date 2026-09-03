import {
  MessageCircle,
  Megaphone,
  Users,
  Layers,
  ShoppingCart,
  BarChart3,
  FileText,
  Settings,
} from "lucide-react";

interface SidebarProps {
  activeItem: string;
  onNavigate: (item: string) => void;
}

const menuItems = [
  {
    id: "chats",
    label: "Chats",
    icon: MessageCircle,
  },
  {
    id: "campaigns",
    label: "Campaigns",
    icon: Megaphone,
  },
  {
    id: "customers",
    label: "Customers",
    icon: Users,
  },
  {
    id: "audience",
    label: "Audience",
    icon: Layers,
  },
  {
    id: "templates",
    label: "Templates",
    icon: FileText,
  },
  {
    id: "orders",
    label: "Orders",
    icon: ShoppingCart,
  },
  {
    id: "analytics",
    label: "Analytics",
    icon: BarChart3,
  },
];

export default function Sidebar({
  activeItem,
  onNavigate,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          W
        </div>

        <span>WhatsApp Business</span>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              className={`sidebar-item ${
                activeItem === item.id ? "active" : ""
              }`}
              onClick={() => onNavigate(item.id)}
            >
              <Icon size={20} strokeWidth={2} />

              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <button
          className={`sidebar-item ${
            activeItem === "settings" ? "active" : ""
          }`}
          onClick={() => onNavigate("settings")}
        >
          <Settings size={20} />

          <span>Settings</span>
        </button>
      </div>
    </aside>
  );
}