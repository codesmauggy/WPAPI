import type { Campaign } from "../../types/campaign";
import CampaignStatusBadge from "./CampaignStatusBadge";

interface Props {
  campaigns: Campaign[];
  selectedCampaignId: number | null;
  onSelect: (campaign: Campaign) => void;
}

export default function CampaignList({
  campaigns,
  selectedCampaignId,
  onSelect,
}: Props) {
  if (campaigns.length === 0) {
    return (
      <div className="empty-state">
        <h3>No campaigns yet</h3>

        <p>
          Create your first WhatsApp campaign to start
          sending messages.
        </p>
      </div>
    );
  }

  return (
    <div className="campaign-list">
      {campaigns.map((campaign) => {
        const stats = campaign.statistics;

        return (
          <button
            key={campaign.id}
            className={`campaign-row ${
              selectedCampaignId === campaign.id
                ? "selected"
                : ""
            }`}
            onClick={() => onSelect(campaign)}
          >
            <div className="campaign-row-main">
              <div className="campaign-avatar">
                <span>📣</span>
              </div>

              <div className="campaign-info">
                <div className="campaign-name">
                  {campaign.name}
                </div>

                <div className="campaign-meta">
                  {campaign.audience?.name ?? "No audience"}
                  {" · "}
                  {campaign.template?.name ?? "No template"}
                </div>
              </div>

              <CampaignStatusBadge
                status={campaign.status}
              />
            </div>

            <div className="campaign-row-stats">
              <span>
                {stats.total} recipients
              </span>

              <span>
                {stats.delivered} delivered
              </span>

              <span>
                {stats.read} read
              </span>

              {stats.failed > 0 && (
                <span className="failed-stat">
                  {stats.failed} failed
                </span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}