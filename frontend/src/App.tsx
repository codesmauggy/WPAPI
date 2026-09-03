import { useCallback, useState } from "react";

import AppShell from "./components/layout/AppShell";
import CampaignsPage from "./pages/Campaigns/CampaignsPage";
import CampaignDetails from "./components/campaigns/CampaignDetails";
import CampaignDeliveryReport from "./components/campaigns/CampaignDeliveryReport";

import type { Campaign } from "./types/campaign";

function App() {
  const [activeItem, setActiveItem] = useState("campaigns");
  const [selectedCampaign, setSelectedCampaign] =
    useState<Campaign | null>(null);

  const [showDeliveryReport, setShowDeliveryReport] =
    useState(false);

  const handleSelectCampaign = useCallback(
    (campaign: Campaign | null) => {
      setSelectedCampaign(campaign);
      setShowDeliveryReport(false);
    },
    []
  );

  const handleCampaignUpdated = useCallback(
    (campaign: Campaign) => {
      setSelectedCampaign(campaign);
    },
    []
  );

  function getPageTitle() {
    switch (activeItem) {
      case "chats":
        return "Chats";
      case "campaigns":
        return showDeliveryReport
          ? "Campaign Delivery Report"
          : "Campaigns";
      case "customers":
        return "Customers";
      case "audience":
        return "Audience";
      case "templates":
        return "Templates";
      case "orders":
        return "Orders";
      case "analytics":
        return "Analytics";
      case "settings":
        return "Settings";
      default:
        return "WhatsApp Business";
    }
  }

  function renderPage() {
    switch (activeItem) {
      case "campaigns":
        if (showDeliveryReport && selectedCampaign) {
          return (
            <CampaignDeliveryReport
              campaign={selectedCampaign}
              onBack={() => setShowDeliveryReport(false)}
              onCampaignUpdated={handleCampaignUpdated}
            />
          );
        }

        return (
          <CampaignsPage
            onSelectCampaign={handleSelectCampaign}
          />
        );

      default:
        return (
          <div className="module-placeholder">
            <h2>{getPageTitle()}</h2>
            <p>This module will be implemented next.</p>
          </div>
        );
    }
  }

  function renderRightPanel() {
    switch (activeItem) {
      case "campaigns":
        return (
          <CampaignDetails
            campaign={selectedCampaign}
            onCampaignUpdated={handleCampaignUpdated}
            onOpenDeliveryReport={() => {
              if (selectedCampaign) {
                setShowDeliveryReport(true);
              }
            }}
          />
        );

      default:
        return null;
    }
  }

  return (
    <AppShell
      activeItem={activeItem}
      title={getPageTitle()}
      onNavigate={(item) => {
        setActiveItem(item);
        setShowDeliveryReport(false);
      }}
      rightPanel={renderRightPanel()}
    >
      {renderPage()}
    </AppShell>
  );
}

export default App;
