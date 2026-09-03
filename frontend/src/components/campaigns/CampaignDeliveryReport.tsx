import {
  useEffect,
  useMemo,
  useState,
} from "react";

import type {
  ReactNode,
} from "react";

import {
  ArrowLeft,
  Ban,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Eye,
  Pause,
  Play,
  RefreshCw,
  Send,
  XCircle,
} from "lucide-react";

import type {
  Campaign,
} from "../../types/campaign";

import {
  cancelCampaign,
  getCampaignRecipients,
  getCampaignStatus,
  pauseCampaign,
  resumeCampaign,
} from "../../api/campaigns";

import type {
  CampaignRecipient,
} from "../../api/campaigns";

import CampaignStatusBadge from "./CampaignStatusBadge";

/* =========================================================
   PROPS
   ========================================================= */

interface Props {
  campaign: Campaign;

  onBack: () => void;

  onCampaignUpdated?: (
    campaign: Campaign
  ) => void;
}

/* =========================================================
   CONSTANTS
   ========================================================= */

const PAGE_SIZE = 25;

/* =========================================================
   COMPONENT
   ========================================================= */

export default function CampaignDeliveryReport({
  campaign,
  onBack,
  onCampaignUpdated,
}: Props) {
  const [
    recipients,
    setRecipients,
  ] = useState<CampaignRecipient[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    busy,
    setBusy,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(null);

  const [
    page,
    setPage,
  ] = useState(1);

  const currentStats =
    campaign.statistics;

  /* =======================================================
     LOAD RECIPIENTS
     ======================================================= */

  async function loadReport() {
    try {
      setLoading(true);
      setError(null);

      const response =
        await getCampaignRecipients(
          campaign.id
        );

      setRecipients(
        response.recipients ?? []
      );

      setPage(1);
    } catch (err: any) {
      console.error(
        "Campaign delivery report failed:",
        err
      );

      setError(
        err?.response?.data?.error ??
          err?.message ??
          "Unable to load campaign delivery report."
      );
    } finally {
      setLoading(false);
    }
  }

  /* =======================================================
     REFRESH STATUS
     ======================================================= */

  async function refreshStatus() {
    try {
      const response =
        await getCampaignStatus(
          campaign.id
        );

      if (!response?.success) {
        return;
      }

      const data =
        response.data;

      const updatedCampaign: Campaign = {
        ...campaign,

        status:
          data.status,

        statistics: {
          ...campaign.statistics,

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
    } catch (err) {
      console.error(
        "Campaign status refresh failed:",
        err
      );
    }
  }

  /* =======================================================
     REFRESH EVERYTHING
     ======================================================= */

  async function refreshAll() {
    await Promise.all([
      loadReport(),
      refreshStatus(),
    ]);
  }

  /* =======================================================
     ACTION RUNNER
     ======================================================= */

  async function runAction(
    action: () => Promise<unknown>
  ) {
    try {
      setBusy(true);
      setError(null);

      await action();

      await refreshAll();
    } catch (err: any) {
      console.error(err);

      setError(
        err?.response?.data?.error ??
          err?.message ??
          "Campaign operation failed."
      );
    } finally {
      setBusy(false);
    }
  }

  /* =======================================================
     LOAD WHEN CAMPAIGN CHANGES
     ======================================================= */

  useEffect(() => {
    void loadReport();
  }, [campaign.id]);

  /* =======================================================
     LIVE POLLING
     ======================================================= */

  useEffect(() => {
    if (
      campaign.status !==
      "RUNNING"
    ) {
      return;
    }

    const interval =
      window.setInterval(() => {
        void refreshAll();
      }, 5000);

    return () =>
      window.clearInterval(
        interval
      );
  }, [
    campaign.id,
    campaign.status,
  ]);

  /* =======================================================
     PAGINATION
     ======================================================= */

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        recipients.length /
          PAGE_SIZE
      )
    );

  const visibleRecipients =
    useMemo(() => {
      const start =
        (page - 1) *
        PAGE_SIZE;

      return recipients.slice(
        start,
        start + PAGE_SIZE
      );
    }, [
      recipients,
      page,
    ]);

  /* =======================================================
     DELIVERY PROGRESS
     ======================================================= */

  /*
   * IMPORTANT:
   *
   * Progress represents delivery only.
   *
   * Delivered / Total * 100
   *
   * Failed recipients do NOT increase progress.
   */

  const progress =
    currentStats.total > 0
      ? Math.min(
          100,
          Math.max(
            0,
            (currentStats.delivered /
              currentStats.total) *
              100
          )
        )
      : 0;

  /* =======================================================
     PAGINATION DISPLAY
     ======================================================= */

  const startNumber =
    recipients.length === 0
      ? 0
      : (page - 1) *
          PAGE_SIZE +
        1;

  const endNumber =
    Math.min(
      page * PAGE_SIZE,
      recipients.length
    );

  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <div className="campaign-delivery-report">

      {/* =================================================
          HEADER
          ================================================= */}

      <div className="delivery-report-header">

        <button
          className="secondary-button"
          onClick={onBack}
        >
          <ArrowLeft size={17} />

          Back to Campaigns
        </button>

        <button
          className="secondary-button"
          onClick={() =>
            void refreshAll()
          }
          disabled={
            loading || busy
          }
        >
          <RefreshCw size={17} />

          Refresh
        </button>

      </div>

      {/* =================================================
          TITLE
          ================================================= */}

      <div className="delivery-report-title">

        <div>

          <div className="delivery-report-title-row">

            <h2>
              {campaign.name}
            </h2>

            <CampaignStatusBadge
              status={
                campaign.status
              }
            />

          </div>

          <p>
            Campaign Delivery Report
          </p>

        </div>

      </div>

      {/* =================================================
          CAMPAIGN INFORMATION
          ================================================= */}

      <div className="delivery-report-info-grid">

        <div>
          <span>
            Audience
          </span>

          <strong>
            {
              campaign
                .audience
                ?.name ?? "—"
            }
          </strong>
        </div>

        <div>
          <span>
            Template
          </span>

          <strong>
            {
              campaign
                .template
                ?.name ?? "—"
            }
          </strong>
        </div>

        <div>
          <span>
            WhatsApp Number
          </span>

          <strong>
            {
              campaign
                .phone_number
                ?.display_phone_number ??
              "—"
            }
          </strong>
        </div>

      </div>

      {/* =================================================
          STATISTICS
          ================================================= */}

      <div className="delivery-report-stats">

        <ReportStat
          icon={
            <UsersIcon />
          }
          label="Total"
          value={
            currentStats.total
          }
        />

        <ReportStat
          icon={
            <Send size={16} />
          }
          label="Sent"
          value={
            currentStats.sent
          }
        />

        <ReportStat
          icon={
            <CheckCircle2 size={16} />
          }
          label="Delivered"
          value={
            currentStats.delivered
          }
        />

        <ReportStat
          icon={
            <Eye size={16} />
          }
          label="Read"
          value={
            currentStats.read
          }
        />

        <ReportStat
          icon={
            <XCircle size={16} />
          }
          label="Failed"
          value={
            currentStats.failed
          }
        />

      </div>

      {/* =================================================
          PROGRESS
          ================================================= */}

      <div className="delivery-report-progress">

        <div className="delivery-report-section-title">

          <h3>
            Progress
          </h3>

          <strong>
            {Math.round(
              progress
            )}
            %
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

        <div className="delivery-report-progress-meta">

          <span>
            {
              currentStats.delivered
            }{" "}
            of{" "}
            {
              currentStats.total
            }{" "}
            delivered
          </span>

          <div className="delivery-report-actions">

            {/* RUNNING */}

            {campaign.status ===
              "RUNNING" && (
              <button
                className="warning-button"
                onClick={() =>
                  void runAction(
                    () =>
                      pauseCampaign(
                        campaign.id
                      )
                  )
                }
                disabled={busy}
              >
                <Pause size={16} />

                Pause
              </button>
            )}

            {/* PAUSED */}

            {campaign.status ===
              "PAUSED" && (
              <button
                className="primary-button"
                onClick={() =>
                  void runAction(
                    () =>
                      resumeCampaign(
                        campaign.id
                      )
                  )
                }
                disabled={busy}
              >
                <Play size={16} />

                Resume
              </button>
            )}

            {/* CANCEL */}

            {(
              campaign.status ===
                "RUNNING" ||
              campaign.status ===
                "PAUSED" ||
              campaign.status ===
                "SCHEDULED"
            ) && (
              <button
                className="danger-button"
                onClick={() => {

                  if (
                    window.confirm(
                      "Are you sure you want to cancel this campaign?"
                    )
                  ) {
                    void runAction(
                      () =>
                        cancelCampaign(
                          campaign.id
                        )
                    );
                  }

                }}
                disabled={busy}
              >
                <Ban size={16} />

                Cancel
              </button>
            )}

          </div>

        </div>

      </div>

      {/* =================================================
          RECIPIENT TABLE
          ================================================= */}

      <div className="delivery-report-table-card">

        <div className="delivery-report-table-header">

          <div>

            <h3>
              Recipients
            </h3>

            <span>
              {
                recipients.length
              }{" "}
              recipients
            </span>

          </div>

        </div>

        {error && (
          <div className="campaign-action-error">

            <XCircle size={15} />

            <span>
              {error}
            </span>

          </div>
        )}

        {loading ? (

          <div className="loading-state">
            Loading recipients...
          </div>

        ) : recipients.length ===
          0 ? (

          <div className="delivery-report-empty">
            No recipients found
            for this campaign.
          </div>

        ) : (

          <>

            <div className="delivery-report-table">

              {/* TABLE HEADER */}

              <div className="delivery-report-table-row delivery-report-table-head">

                <div>
                  Customer
                </div>

                <div>
                  Phone
                </div>

                <div>
                  Status
                </div>

                <div>
                  Read
                </div>

                <div>
                  Failed
                </div>

              </div>

              {/* TABLE ROWS */}

              {visibleRecipients.map(
                (
                  recipient
                ) => (

                  <div
                    key={
                      recipient.id
                    }
                    className="delivery-report-table-row"
                  >

                    {/* CUSTOMER */}

                    <div className="recipient-customer">

                      <strong>
                        {
                          recipient
                            .customer
                            ?.name ??
                          "Unknown Customer"
                        }
                      </strong>

                    </div>

                    {/* PHONE */}

                    <div>
                      {
                        recipient.phone
                      }
                    </div>

                    {/* STATUS */}

                    <div>

                      <span
                        className={`delivery-status status-${recipient.status.toLowerCase()}`}
                      >
                        {
                          recipient.status
                        }
                      </span>

                    </div>

                    {/* READ */}

                    <div>

                      {
                        recipient.read_at ? (
                          <CheckCircle2
                            size={16}
                          />
                        ) : (
                          "—"
                        )
                      }

                    </div>

                    {/* FAILED */}

                    <div>

                      {
                        recipient.failed_at ? (
                          <XCircle
                            size={16}
                          />
                        ) : (
                          "—"
                        )
                      }

                    </div>

                  </div>

                )
              )}

            </div>

            {/* PAGINATION */}

            <div className="delivery-report-pagination">

              <span>
                Showing{" "}
                {startNumber}
                –
                {endNumber}
                {" "}
                of{" "}
                {
                  recipients.length
                }
              </span>

              <div>

                <button
                  className="icon-button"
                  onClick={() =>
                    setPage(
                      (value) =>
                        Math.max(
                          1,
                          value - 1
                        )
                    )
                  }
                  disabled={
                    page === 1
                  }
                  aria-label="Previous page"
                >
                  <ChevronLeft
                    size={18}
                  />
                </button>

                <span className="delivery-report-page-number">
                  Page{" "}
                  {page}{" "}
                  of{" "}
                  {
                    totalPages
                  }
                </span>

                <button
                  className="icon-button"
                  onClick={() =>
                    setPage(
                      (value) =>
                        Math.min(
                          totalPages,
                          value + 1
                        )
                    )
                  }
                  disabled={
                    page ===
                    totalPages
                  }
                  aria-label="Next page"
                >
                  <ChevronRight
                    size={18}
                  />
                </button>

              </div>

            </div>

          </>

        )}

      </div>

    </div>
  );
}

/* =========================================================
   REPORT STAT
   ========================================================= */

function ReportStat({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div className="delivery-report-stat">

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
   USERS ICON
   ========================================================= */

function UsersIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle
        cx="9"
        cy="7"
        r="4"
      />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}