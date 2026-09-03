import type { CampaignStatus } from "../../types/campaign";

interface Props {
  status: CampaignStatus;
}

export default function CampaignStatusBadge({
  status,
}: Props) {
  const label = status.replace("_", " ");

  return (
    <span
      className={`campaign-status campaign-status-${status.toLowerCase()}`}
    >
      <span className="status-dot" />

      {label}
    </span>
  );
}