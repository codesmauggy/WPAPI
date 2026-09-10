import {
  useCallback,
  useState,
} from "react";

import {
  useLocation,
  useNavigate,
} from "react-router-dom";

import AppShell from "./components/layout/AppShell";

import CampaignsPage from "./pages/Campaigns/CampaignsPage";
import ChatsPage from "./pages/Chats/ChatsPage";
import CustomersPage from "./pages/Customers/CustomersPage";
import AudiencePage from "./pages/Audience/AudiencePage";

import CampaignDetails from "./components/campaigns/CampaignDetails";
import CampaignDeliveryReport from "./components/campaigns/CampaignDeliveryReport";
import ChatCustomerPanel from "./components/chat/ChatCustomerPanel";
import CustomerDetails from "./components/customer/CustomerDetails";
import AudienceDetails from "./components/audience/AudienceDetails";

import type { Campaign } from "./types/campaign";
import type { Conversation } from "./types/chat";
import type { Customer } from "./types/customer";
import type {
  Audience,
} from "./types/audience";

// =========================================================
// ROUTES
// =========================================================

const routeMap: Record<
  string,
  string
> = {
  Campaigns: "/Campaigns",
  Chats: "/Chats",
  Customers: "/Customers",
  Audience: "/Audience",
  Templates: "/Templates",
  Orders: "/Orders",
  Analytics: "/Analytics",
  Settings: "/Settings",
};

// =========================================================
// APP
// =========================================================

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  // =======================================================
  // STATE
  // =======================================================

  const [selectedCampaign, setSelectedCampaign] =
    useState<Campaign | null>(null);

  const [
    showDeliveryReport,
    setShowDeliveryReport,
  ] = useState(false);

  const [
    selectedConversation,
    setSelectedConversation,
  ] = useState<Conversation | null>(
    null,
  );

  const [
    selectedCustomer,
    setSelectedCustomer,
  ] = useState<Customer | null>(
    null,
  );

  const [
    selectedAudience,
    setSelectedAudience,
  ] = useState<Audience | null>(
    null,
  );

  // =======================================================
  // CURRENT ROUTE
  // =======================================================

  const pathname =
    location.pathname.replace(
      /^\/+/,
      "",
    );

  const routeName =
    pathname.split("/")[0] ||
    "Campaigns";

  const activeItem =
    routeName.toLowerCase();

  const audienceIdFromUrl =
    activeItem === "audience"
      ? Number(
          new URLSearchParams(
            location.search,
          ).get("audienceId"),
        ) || null
      : null;
      
  // =======================================================
  // NAVIGATION
  // =======================================================

  const handleNavigate =
    useCallback(
      (item: string) => {
        const route =
          Object.keys(routeMap).find(
            (key) =>
              key.toLowerCase() ===
              item.toLowerCase(),
          );

        if (!route) {
          return;
        }

        setShowDeliveryReport(false);

        navigate(
          routeMap[route],
        );
      },
      [navigate],
    );

  // =======================================================
  // CAMPAIGN
  // =======================================================

  const handleSelectCampaign =
    useCallback(
      (
        campaign: Campaign | null,
      ) => {
        setSelectedCampaign(
          campaign,
        );

        setShowDeliveryReport(
          false,
        );
      },
      [],
    );

  const handleCampaignUpdated =
    useCallback(
      (campaign: Campaign) => {
        setSelectedCampaign(
          campaign,
        );
      },
      [],
    );

  // =======================================================
  // CONVERSATION
  // =======================================================

  const handleConversationSelected =
    useCallback(
      (
        conversation:
          | Conversation
          | null,
      ) => {
        setSelectedConversation(
          conversation,
        );
      },
      [],
    );

  // =======================================================
  // AUDIENCE
  // =======================================================

  const handleAudienceSelected =
    useCallback(
      (audience: Audience | null) => {
        setSelectedAudience(audience);

        if (!audience) {
          if (activeItem === "audience") {
            navigate("/Audience", {
              replace: true,
            });
          }

          return;
        }

        navigate(
          `/Audience?audienceId=${audience.id}`,
          {
            replace: true,
          },
        );
      },
      [activeItem, navigate],
    );

  const handleAudienceUpdated =
    useCallback(
      (audience: Audience) => {
        setSelectedAudience(audience);
      },
      [],
    );

  const handleAudienceDeleted =
    useCallback(
      (audienceId: number) => {
        setSelectedAudience(
          (current) =>
            current?.id === audienceId
              ? null
              : current,
        );

        if (activeItem === "audience") {
          navigate("/Audience", {
            replace: true,
          });
        }
      },
      [activeItem, navigate],
    );  

  // =======================================================
  // CUSTOMER
  // =======================================================

  const handleCustomerSelected =
    useCallback(
      (
        customer:
          | Customer
          | null,
      ) => {
        setSelectedCustomer(
          customer,
        );
      },
      [],
    );

  const handleCustomerUpdated =
    useCallback(
      (
        customer: Customer,
      ) => {
        setSelectedCustomer(
          customer,
        );
      },
      [],
    );

  // =======================================================
  // PAGE TITLE
  // =======================================================

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
        return "Campaigns";
    }
  }

  // =======================================================
  // PAGE CONTENT
  // =======================================================

  function renderPage() {
    switch (activeItem) {
      // -----------------------------------------------------
      // AUDIENCE
      // -----------------------------------------------------

      case "audience":
        return (
          <AudiencePage
            selectedAudience={selectedAudience}
            initialAudienceId={
              audienceIdFromUrl
            }
            onAudienceSelected={
              handleAudienceSelected
            }
          />
        );
      // -----------------------------------------------------
      // CHATS
      // -----------------------------------------------------

      case "chats":
        return (
          <ChatsPage
            onConversationSelected={
              handleConversationSelected
            }
          />
        );

      // -----------------------------------------------------
      // CAMPAIGNS
      // -----------------------------------------------------

      case "campaigns":
        if (
          showDeliveryReport &&
          selectedCampaign
        ) {
          return (
            <CampaignDeliveryReport
              campaign={
                selectedCampaign
              }
              onBack={() =>
                setShowDeliveryReport(
                  false,
                )
              }
              onCampaignUpdated={
                handleCampaignUpdated
              }
            />
          );
        }

        return (
          <CampaignsPage
            onSelectCampaign={
              handleSelectCampaign
            }
          />
        );

      // -----------------------------------------------------
      // CUSTOMERS
      // -----------------------------------------------------

      case "customers":
        return (
          <CustomersPage
            selectedCustomer={
              selectedCustomer
            }
            onCustomerSelected={
              handleCustomerSelected
            }
          />
        );

      // -----------------------------------------------------
      // AUDIENCE
      // -----------------------------------------------------

      // case "audience":
      //   return (
      //     <AudiencePage />
      //   );

      // -----------------------------------------------------
      // OTHER MODULES
      // -----------------------------------------------------

      default:
        return (
          <div className="module-placeholder">
            <h2>
              {getPageTitle()}
            </h2>

            <p>
              This module will be
              implemented next.
            </p>
          </div>
        );
    }
  }

  // =======================================================
  // RIGHT BUSINESS OPERATIONS PANEL
  // =======================================================

  function renderRightPanel() {
    switch (activeItem) {
      // -----------------------------------------------------
      // CHATS
      // -----------------------------------------------------

      case "chats":
        return (
          <ChatCustomerPanel
            conversation={
              selectedConversation
            }
          />
        );

      // -----------------------------------------------------
      // CAMPAIGNS
      // -----------------------------------------------------

      case "campaigns":
        return (
          <CampaignDetails
            campaign={
              selectedCampaign
            }
            onCampaignUpdated={
              handleCampaignUpdated
            }
            onOpenDeliveryReport={() => {
              if (
                selectedCampaign
              ) {
                setShowDeliveryReport(
                  true,
                );
              }
            }}
          />
        );

      // -----------------------------------------------------
      // CUSTOMERS
      // -----------------------------------------------------

      case "customers":
        return (
          <CustomerDetails
            customer={selectedCustomer}
            onOpenChat={(customer) => {
              navigate(
                `/Chats?customerId=${customer.id}`,
              );
            }}
            onCustomerUpdated={
              handleCustomerUpdated
            }
          />
        );

      // -----------------------------------------------------
      // AUDIENCE
      // -----------------------------------------------------

      case "audience":
        return (
          <AudienceDetails
            audience={selectedAudience}
            onAudienceUpdated={
              handleAudienceUpdated
            }
            onAudienceDeleted={
              handleAudienceDeleted
            }
          />
        );  

      // -----------------------------------------------------
      // OTHER MODULES
      // -----------------------------------------------------

      default:
        return null;
    }
  }

  // =======================================================
  // APP SHELL
  // =======================================================

  return (
    <AppShell
      activeItem={
        activeItem
      }
      title={getPageTitle()}
      onNavigate={
        handleNavigate
      }
      rightPanel={
        renderRightPanel()
      }
    >
      {renderPage()}
    </AppShell>
  );
}

export default App;