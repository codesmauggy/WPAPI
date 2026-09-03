import {
  useState,
} from "react";

import {
  Users,
  FileText,
  Smartphone,
  CheckCircle2,
  Send,
  Eye,
  XCircle,
  Play,
  Pause,
  Ban,
  RefreshCw,
  UserPlus,
} from "lucide-react";

import type { ReactNode } from "react";

import type { Campaign } from "../../types/campaign";

import {
  generateCampaignRecipients,
  getCampaignStatus,
  pauseCampaign,
  resumeCampaign,
  cancelCampaign,
  queueCampaign,
} from "../../api/campaigns";

// import CampaignStatusBadge from "./CampaignStatusBadge";

/* =========================================================
   PROPS
   ========================================================= */

interface Props {
  campaign: Campaign | null;

  onCampaignUpdated?: (
    campaign: Campaign
  ) => void;

  onOpenDeliveryReport?: () => void;
}

/* =========================================================
   COMPONENT
   ========================================================= */

export default function CampaignDetails({
  campaign,
  onCampaignUpdated,
  onOpenDeliveryReport,
}: Props) {
  const [busy, setBusy] = useState(false);

  const [actionError, setActionError] =
    useState<string | null>(null);

  const [actionMessage, setActionMessage] =
    useState<string | null>(null);

  /* =======================================================
     EMPTY STATE
     ======================================================= */

  if (!campaign) {
    return (
      <div className="right-empty-state">
        <MegaphonePlaceholder />

        <h3>Select a campaign</h3>

        <p>
          Select a campaign to view business
          operations and statistics.
        </p>
      </div>
    );
  }

  /*
   * Stable non-null reference.
   */
  const currentCampaign = campaign;

  /* =======================================================
     NORMALIZE STATISTICS
     ======================================================= */

  const toSafeNumber = (
    value: unknown
  ): number => {
    const number = Number(value);

    return Number.isFinite(number)
      ? number
      : 0;
  };

  const stats = {
    total: toSafeNumber(
      currentCampaign.statistics?.total
    ),

    pending: toSafeNumber(
      currentCampaign.statistics?.pending
    ),

    sending: toSafeNumber(
      currentCampaign.statistics?.sending
    ),

    sent: toSafeNumber(
      currentCampaign.statistics?.sent
    ),

    delivered: toSafeNumber(
      currentCampaign.statistics?.delivered
    ),

    read: toSafeNumber(
      currentCampaign.statistics?.read
    ),

    failed: toSafeNumber(
      currentCampaign.statistics?.failed
    ),

    cancelled: toSafeNumber(
      currentCampaign.statistics?.cancelled
    ),

    completed: toSafeNumber(
      currentCampaign.statistics?.completed
    ),
  };

  /* =======================================================
     REFRESH STATUS
     ======================================================= */

  async function refreshCampaignStatus() {
    const response =
      await getCampaignStatus(
        currentCampaign.id
      );

    if (!response?.success) {
      throw new Error(
        response?.error ??
          "Unable to refresh campaign status."
      );
    }

    const data = response.data;

    const updatedCampaign: Campaign = {
      ...currentCampaign,

      status: data.status,

      statistics: {
        ...currentCampaign.statistics,

        total:
          Number(
            data.statistics?.total ?? 0
          ),

        pending:
          Number(
            data.statistics?.pending ?? 0
          ),

        sending:
          Number(
            data.statistics?.sending ?? 0
          ),

        sent:
          Number(
            data.statistics?.sent ?? 0
          ),

        delivered:
          Number(
            data.statistics?.delivered ?? 0
          ),

        read:
          Number(
            data.statistics?.read ?? 0
          ),

        failed:
          Number(
            data.statistics?.failed ?? 0
          ),

        cancelled:
          Number(
            data.statistics?.cancelled ?? 0
          ),

        completed:
          Number(
            data.statistics?.completed ?? 0
          ),
      },
    };

    onCampaignUpdated?.(
      updatedCampaign
    );
  }

  /* =======================================================
     GENERIC ACTION RUNNER
     ======================================================= */

  async function runAction(
    action: () => Promise<unknown>,
    successMessage: string
  ) {
    try {
      setBusy(true);

      setActionError(null);
      setActionMessage(null);

      await action();

      setActionMessage(
        successMessage
      );

      await refreshCampaignStatus();
    } catch (error: any) {
      console.error(error);

      const message =
        error?.response?.data?.error ??
        error?.message ??
        "Campaign operation failed.";

      setActionError(message);
    } finally {
      setBusy(false);
    }
  }

  /* =======================================================
     GENERATE RECIPIENTS
     ======================================================= */

  function handleGenerateRecipients() {
    return runAction(
      () =>
        generateCampaignRecipients(
          currentCampaign.id
        ),

      "Recipients generated successfully."
    );
  }

  /* =======================================================
     QUEUE
     ======================================================= */

  function handleQueue() {
    return runAction(
      () =>
        queueCampaign(
          currentCampaign.id
        ),

      "Campaign queued successfully."
    );
  }

  /* =======================================================
     PAUSE
     ======================================================= */

  function handlePause() {
    return runAction(
      () =>
        pauseCampaign(
          currentCampaign.id
        ),

      "Campaign paused successfully."
    );
  }

  /* =======================================================
     RESUME
     ======================================================= */

  function handleResume() {
    return runAction(
      () =>
        resumeCampaign(
          currentCampaign.id
        ),

      "Campaign resumed successfully."
    );
  }

  /* =======================================================
     CANCEL
     ======================================================= */

  function handleCancel() {
    const confirmed =
      window.confirm(
        "Are you sure you want to cancel this campaign?"
      );

    if (!confirmed) {
      return;
    }

    return runAction(
      () =>
        cancelCampaign(
          currentCampaign.id
        ),

      "Campaign cancelled successfully."
    );
  }

  /* =======================================================
     DELIVERY PROGRESS
     ======================================================= */

  /*
   * IMPORTANT:
   *
   * Progress represents delivery progress only.
   *
   * Delivered / Total * 100
   *
   * Failed recipients do NOT increase progress.
   */

  const progress =
    stats.total > 0
      ? Math.min(
          100,
          Math.max(
            0,
            (stats.delivered /
              stats.total) *
              100
          )
        )
      : 0;

  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <div className="campaign-details">

      {/* =================================================
          HEADER
          ================================================= */}

      {/* <div className="details-header">

        <div className="large-campaign-avatar">
          📣
        </div>

        <h3>
          {currentCampaign.name}
        </h3>

        <CampaignStatusBadge
          status={
            currentCampaign.status
          }
        />

      </div> */}

      {/* =================================================
          ACTION FEEDBACK
          ================================================= */}

      {actionMessage && (
        <div className="campaign-action-success">

          <CheckCircle2 size={15} />

          <span>
            {actionMessage}
          </span>

        </div>
      )}

      {actionError && (
        <div className="campaign-action-error">

          <XCircle size={15} />

          <span>
            {actionError}
          </span>

        </div>
      )}

      {/* =================================================
          CAMPAIGN INFORMATION
          ================================================= */}

      <div className="details-section">

        <h4>
          Campaign Information
        </h4>

        <DetailRow
          icon={
            <Users size={17} />
          }
          label="Audience"
          value={
            currentCampaign
              .audience?.name ??
            "—"
          }
        />

        <DetailRow
          icon={
            <FileText size={17} />
          }
          label="Template"
          value={
            currentCampaign
              .template?.name ??
            "—"
          }
        />

        <DetailRow
          icon={
            <Smartphone size={17} />
          }
          label="WhatsApp Number"
          value={
            currentCampaign
              .phone_number
              ?.display_phone_number ??
            "—"
          }
        />

        {onOpenDeliveryReport && (
          <button
            type="button"
            className="primary-button campaign-view-button"
            onClick={
              onOpenDeliveryReport
            }
          >
            <FileText size={16} />
            View Campaign
          </button>
        )}

      </div>

      {/* =================================================
          STATISTICS
          ================================================= */}

      <div className="details-section">

        <h4>
          Statistics
        </h4>

        <div className="stats-grid">

          <StatCard
            icon={
              <Users size={17} />
            }
            label="Total"
            value={stats.total}
          />

          <StatCard
            icon={
              <Send size={17} />
            }
            label="Sent"
            value={stats.sent}
          />

          <StatCard
            icon={
              <CheckCircle2 size={17} />
            }
            label="Delivered"
            value={
              stats.delivered
            }
          />

          <StatCard
            icon={
              <Eye size={17} />
            }
            label="Read"
            value={stats.read}
          />

          <StatCard
            icon={
              <XCircle size={17} />
            }
            label="Failed"
            value={
              stats.failed
            }
          />

        </div>

      </div>

      {/* =================================================
          PROGRESS
          ================================================= */}

      <div className="details-section">

        <div className="details-section-header">

          <h4>
            Progress
          </h4>

          <strong>
            {Math.round(progress)}%
          </strong>

        </div>

        <div className="progress-bar">

          <div
            className="progress-fill"
            style={{
              width: `${progress}%`,
            }}
          />

        </div>

        <div className="progress-text">
          {stats.delivered} / {stats.total} delivered
        </div>

      </div>

      {/* =================================================
          ACTIONS
          ================================================= */}

      <div className="details-section">

        <h4>
          Actions
        </h4>

        {/* ===============================================
            DRAFT
            =============================================== */}

        {currentCampaign.status ===
          "DRAFT" && (
          <div className="campaign-actions">

            <button
              className="secondary-button"
              onClick={
                handleGenerateRecipients
              }
              disabled={busy}
            >
              <UserPlus size={16} />

              Generate Recipients
            </button>

            <button
              className="primary-button"
              onClick={handleQueue}
              disabled={
                busy ||
                stats.pending === 0
              }
              title={
                stats.pending === 0
                  ? "Generate recipients before queueing the campaign."
                  : "Queue campaign"
              }
            >
              <Play size={16} />

              Queue Campaign
            </button>

          </div>
        )}

        {/* ===============================================
            SCHEDULED
            =============================================== */}

        {currentCampaign.status ===
          "SCHEDULED" && (
          <div className="campaign-actions">

            <button
              className="primary-button"
              onClick={handleQueue}
              disabled={busy}
            >
              <Play size={16} />

              Start Campaign
            </button>

            <button
              className="danger-button"
              onClick={handleCancel}
              disabled={busy}
            >
              <Ban size={16} />

              Cancel
            </button>

          </div>
        )}

        {/* ===============================================
            RUNNING
            =============================================== */}

        {currentCampaign.status ===
          "RUNNING" && (
          <div className="campaign-actions">

            <button
              className="warning-button"
              onClick={handlePause}
              disabled={busy}
            >
              <Pause size={16} />

              Pause
            </button>

            <button
              className="danger-button"
              onClick={handleCancel}
              disabled={busy}
            >
              <Ban size={16} />

              Cancel
            </button>

          </div>
        )}

        {/* ===============================================
            PAUSED
            =============================================== */}

        {currentCampaign.status ===
          "PAUSED" && (
          <div className="campaign-actions">

            <button
              className="primary-button"
              onClick={handleResume}
              disabled={busy}
            >
              <Play size={16} />

              Resume
            </button>

            <button
              className="danger-button"
              onClick={handleCancel}
              disabled={busy}
            >
              <Ban size={16} />

              Cancel
            </button>

          </div>
        )}

        {/* ===============================================
            COMPLETED
            =============================================== */}

        {currentCampaign.status ===
          "COMPLETED" && (
          <div className="campaign-completed-message">

            <CheckCircle2 size={18} />

            <span>
              Campaign completed.
            </span>

          </div>
        )}

        {/* ===============================================
            CANCELLED
            =============================================== */}

        {currentCampaign.status ===
          "CANCELLED" && (
          <div className="campaign-cancelled-message">

            <Ban size={18} />

            <span>
              Campaign cancelled.
            </span>

          </div>
        )}

        {/* ===============================================
            FAILED
            =============================================== */}

        {currentCampaign.status ===
          "FAILED" && (
          <div className="campaign-error-message">

            <XCircle size={18} />

            <span>
              Campaign failed.
            </span>

          </div>
        )}

        {/* ===============================================
            LOADING
            =============================================== */}

        {busy && (
          <div className="campaign-operation-loading">

            <RefreshCw
              size={14}
              className="spin"
            />

            Processing...

          </div>
        )}

      </div>

    </div>
  );
}

/* =========================================================
   DETAIL ROW
   ========================================================= */

function DetailRow({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="detail-row">

      <div className="detail-row-icon">
        {icon}
      </div>

      <div>

        <div className="detail-label">
          {label}
        </div>

        <div className="detail-value">
          {value}
        </div>

      </div>

    </div>
  );
}

/* =========================================================
   STAT CARD
   ========================================================= */

function StatCard({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div className="stat-card">

      {icon}

      <strong>
        {value}
      </strong>

      <span>
        {label}
      </span>

    </div>
  );
}

/* =========================================================
   EMPTY PLACEHOLDER
   ========================================================= */

function MegaphonePlaceholder() {
  return (
    <div className="right-placeholder-icon">
      📣
    </div>
  );
}