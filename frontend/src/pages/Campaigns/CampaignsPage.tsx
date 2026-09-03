import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Plus,
  RefreshCw,
} from "lucide-react";

import CampaignList from "../../components/campaigns/CampaignList";

import {
  getCampaigns,
  getCampaignStatus,
} from "../../api/campaigns";

import NewCampaignPanel from "../../components/campaigns/NewCampaignPanel";

import type {
  CreateCampaignResponse,
} from "../../api/campaigns";

import type { Campaign } from "../../types/campaign";

/* =========================================================
   PROPS
   ========================================================= */

interface CampaignsPageProps {
  onSelectCampaign: (
    campaign: Campaign | null
  ) => void;
}

/* =========================================================
   COMPONENT
   ========================================================= */

export default function CampaignsPage({
  onSelectCampaign,
}: CampaignsPageProps) {
  const [campaigns, setCampaigns] =
    useState<Campaign[]>([]);

  const [selectedCampaign, setSelectedCampaign] =
    useState<Campaign | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [showNewCampaign, setShowNewCampaign] =
    useState(false);

  /*
   * Keep a ref to the selected campaign.
   *
   * This lets loadCampaigns() access the latest
   * selected campaign without making loadCampaigns()
   * depend on selectedCampaign.
   */
  const selectedCampaignRef =
    useRef<Campaign | null>(null);

  /* =======================================================
     SELECT CAMPAIGN
     ======================================================= */

  function handleSelectCampaign(
    campaign: Campaign
  ) {
    setSelectedCampaign(
      campaign
    );

    selectedCampaignRef.current =
      campaign;

    onSelectCampaign(
      campaign
    );
  }

  /* =======================================================
     LOAD CAMPAIGNS
     ======================================================= */

  const loadCampaigns =
    useCallback(async () => {
      try {
        setLoading(true);
        setError(null);

        const data =
          await getCampaigns();

        setCampaigns(data);

        /*
         * Synchronize currently selected campaign
         * with the latest campaign list.
         */

        const currentSelected =
          selectedCampaignRef.current;

        if (currentSelected) {
          const updated =
            data.find(
              (item) =>
                item.id ===
                currentSelected.id
            );

          if (updated) {
            setSelectedCampaign(
              updated
            );

            selectedCampaignRef.current =
              updated;

            onSelectCampaign(
              updated
            );
          } else {
            setSelectedCampaign(
              null
            );

            selectedCampaignRef.current =
              null;

            onSelectCampaign(
              null
            );
          }
        }
      } catch (err) {
        console.error(
          "Unable to load campaigns:",
          err
        );

        setError(
          "Unable to load campaigns. Please check the API."
        );
      } finally {
        setLoading(false);
      }
    }, [onSelectCampaign]);

  /* =======================================================
     INITIAL LOAD
     ======================================================= */

  useEffect(() => {
    void loadCampaigns();
  }, [loadCampaigns]);

  /* =======================================================
     UPDATE CAMPAIGN FROM STATUS API
     ======================================================= */

  const refreshSelectedStatus =
    useCallback(async () => {
      const currentSelected =
        selectedCampaignRef.current;

      if (!currentSelected) {
        return;
      }

      try {
        const response =
          await getCampaignStatus(
            currentSelected.id
          );

        if (!response?.success) {
          return;
        }

        const data =
          response.data;

        const updatedCampaign: Campaign =
          {
            ...currentSelected,

            status:
              data.status,

            statistics: {
              ...currentSelected.statistics,

              total:
                data.statistics.total,

              pending:
                data.statistics.pending,

              sending:
                data.statistics.sending,

              sent:
                data.statistics.sent,

              delivered:
                data.statistics.delivered,

              read:
                data.statistics.read,

              failed:
                data.statistics.failed,

              cancelled:
                data.statistics.cancelled,

              completed:
                data.statistics.completed,
            },
          };

        /*
         * Update selected campaign ref FIRST.
         */

        selectedCampaignRef.current =
          updatedCampaign;

        /*
         * Update campaign list.
         */

        setCampaigns(
          (current) =>
            current.map(
              (item) =>
                item.id ===
                updatedCampaign.id
                  ? updatedCampaign
                  : item
            )
        );

        /*
         * Update selected campaign.
         */

        setSelectedCampaign(
          updatedCampaign
        );

        /*
         * Update App.tsx right panel.
         */

        onSelectCampaign(
          updatedCampaign
        );
      } catch (err) {
        console.error(
          "Campaign status refresh failed:",
          err
        );
      }
    }, [onSelectCampaign]);

  /* =======================================================
     LIVE POLLING
     ======================================================= */

  useEffect(() => {
    if (
      !selectedCampaign ||
      selectedCampaign.status !==
        "RUNNING"
    ) {
      return;
    }

    /*
     * Refresh immediately.
     */

    void refreshSelectedStatus();

    /*
     * Then refresh every 5 seconds.
     */

    const interval =
      window.setInterval(() => {
        void refreshSelectedStatus();
      }, 5000);

    return () => {
      window.clearInterval(
        interval
      );
    };
  }, [
    selectedCampaign?.id,
    selectedCampaign?.status,
    refreshSelectedStatus,
  ]);

  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <div className="campaigns-page">

      {/* =================================================
          TOOLBAR
          ================================================= */}

      <div className="page-toolbar">

        <div>

          <h2>
            Campaigns
          </h2>

          <p>
            Manage WhatsApp marketing campaigns
          </p>

        </div>

        <div className="toolbar-actions">

          <button
            className="secondary-button"
            onClick={() =>
              void loadCampaigns()
            }
            disabled={loading}
          >
            <RefreshCw
              size={17}
            />

            Refresh
          </button>

          <button
            className="primary-button"
            onClick={() =>
              setShowNewCampaign(true)
            }
          >
            <Plus size={18} />
            New Campaign
          </button>

        </div>

      </div>

      {/* =================================================
          CONTENT
          ================================================= */}

      {showNewCampaign ? (
        <NewCampaignPanel
          onCancel={() =>
            setShowNewCampaign(false)
          }
          onCreated={async (
            result: CreateCampaignResponse
          ) => {
            console.log("Campaign created:", result);

            setShowNewCampaign(false);

            try {
              setError(null);
              const data = await getCampaigns();
              setCampaigns(data);

              const createdCampaign = data.find(
                (item) => item.id === result.campaign_id
              );

              if (createdCampaign) {
                setSelectedCampaign(createdCampaign);
                selectedCampaignRef.current = createdCampaign;
                onSelectCampaign(createdCampaign);
              }
            } catch (err) {
              console.error(
                "Unable to load newly created campaign:",
                err
              );
              setError(
                "Campaign was created, but the new campaign could not be loaded."
              );
            }
          }}
        />
      ) : loading ? (
        <div className="loading-state">
          Loading campaigns...
        </div>
      ) : error ? (
        <div className="error-state">
          {error}
        </div>
      ) : (
        <CampaignList
          campaigns={campaigns}
          selectedCampaignId={
            selectedCampaign?.id ??
            null
          }
          onSelect={
            handleSelectCampaign
          }
        />
      )}

    </div>
  );
}