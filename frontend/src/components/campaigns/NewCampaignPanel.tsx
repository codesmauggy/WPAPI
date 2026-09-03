import {
  useEffect,
  useState,
} from "react";

import type {
  FormEvent,
} from "react";

import {
  ArrowLeft,
  Megaphone,
  Smartphone,
  Users,
  FileText,
  RefreshCw,
  Plus,
} from "lucide-react";

import {
  createCampaign,
  getCampaignOptions,
} from "../../api/campaigns";

import type {
  CampaignOptions,
  CreateCampaignResponse,
} from "../../api/campaigns";

interface Props {
  onCreated: (result: CreateCampaignResponse) => void;
  onCancel: () => void;
}

export default function NewCampaignPanel({
  onCreated,
  onCancel,
}: Props) {
  const [options, setOptions] =
    useState<CampaignOptions | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [name, setName] =
    useState("");

  const [phoneNumberId, setPhoneNumberId] =
    useState("");

  const [audienceId, setAudienceId] =
    useState("");

  const [templateId, setTemplateId] =
    useState("");

  useEffect(() => {
    async function loadOptions() {
      try {
        setLoading(true);
        setError(null);

        const data =
          await getCampaignOptions();

        setOptions(data);
      } catch (err: any) {
        console.error(
          "Unable to load campaign options:",
          err
        );

        setError(
          err?.response?.data?.error ??
            err?.message ??
            "Unable to load campaign options."
        );
      } finally {
        setLoading(false);
      }
    }

    void loadOptions();
  }, []);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError(null);

    if (!name.trim()) {
      setError(
        "Please enter a campaign name."
      );
      return;
    }

    if (!phoneNumberId) {
      setError(
        "Please select a WhatsApp number."
      );
      return;
    }

    if (!audienceId) {
      setError(
        "Please select an audience."
      );
      return;
    }

    if (!templateId) {
      setError(
        "Please select a template."
      );
      return;
    }

    try {
      setSubmitting(true);

      const result =
        await createCampaign({
          name: name.trim(),
          phone_number_id:
            Number(phoneNumberId),
          audience_id:
            Number(audienceId),
          template_id:
            Number(templateId),
        });

      onCreated(result);
    } catch (err: any) {
      console.error(
        "Campaign creation failed:",
        err
      );

      setError(
        err?.response?.data?.error ??
          err?.message ??
          "Unable to create campaign."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="new-campaign-panel">
        <div className="new-campaign-header">
          <button
            type="button"
            className="icon-button"
            onClick={onCancel}
          >
            <ArrowLeft size={18} />
          </button>

          <div>
            <h3>New Campaign</h3>
            <p>
              Create a WhatsApp marketing campaign
            </p>
          </div>
        </div>

        <div className="new-campaign-loading">
          <RefreshCw
            size={20}
            className="spin"
          />

          <span>
            Loading campaign options...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="new-campaign-panel">

      {/* HEADER */}

      <div className="new-campaign-header">

        <button
          type="button"
          className="icon-button"
          onClick={onCancel}
          disabled={submitting}
        >
          <ArrowLeft size={18} />
        </button>

        <div className="new-campaign-title-icon">
          <Megaphone size={18} />
        </div>

        <div>
          <h3>New Campaign</h3>

          <p>
            Create a WhatsApp marketing campaign
          </p>
        </div>

      </div>

      {/* ERROR */}

      {error && (
        <div className="campaign-action-error">
          <span>{error}</span>
        </div>
      )}

      {/* FORM */}

      <form
        className="new-campaign-form"
        onSubmit={handleSubmit}
      >

        {/* CAMPAIGN NAME */}

        <div className="form-group">

          <label>
            Campaign Name
          </label>

          <div className="form-input-wrapper">
            <Megaphone size={17} />

            <input
              type="text"
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              placeholder="Enter campaign name"
              disabled={submitting}
              autoFocus
            />
          </div>

        </div>

        {/* WHATSAPP NUMBER */}

        <div className="form-group">

          <label>
            WhatsApp Number
          </label>

          <div className="form-input-wrapper">

            <Smartphone size={17} />

            <select
              value={phoneNumberId}
              onChange={(event) =>
                setPhoneNumberId(
                  event.target.value
                )
              }
              disabled={submitting}
            >

              <option value="">
                Select WhatsApp number
              </option>

              {options?.phone_numbers.map(
                (phone) => (
                  <option
                    key={phone.id}
                    value={phone.id}
                  >
                    {phone.display_name}{" "}
                    ({phone.phone_number})
                  </option>
                )
              )}

            </select>

          </div>

        </div>

        {/* AUDIENCE */}

        <div className="form-group">

          <label>
            Audience
          </label>

          <div className="form-input-wrapper">

            <Users size={17} />

            <select
              value={audienceId}
              onChange={(event) =>
                setAudienceId(
                  event.target.value
                )
              }
              disabled={submitting}
            >

              <option value="">
                Select audience
              </option>

              {options?.audiences.map(
                (audience) => (
                  <option
                    key={audience.id}
                    value={audience.id}
                  >
                    {audience.name}
                  </option>
                )
              )}

            </select>

          </div>

        </div>

        {/* TEMPLATE */}

        <div className="form-group">

          <label>
            Approved Template
          </label>

          <div className="form-input-wrapper">

            <FileText size={17} />

            <select
              value={templateId}
              onChange={(event) =>
                setTemplateId(
                  event.target.value
                )
              }
              disabled={submitting}
            >

              <option value="">
                Select approved template
              </option>

              {options?.templates.map(
                (template) => (
                  <option
                    key={template.id}
                    value={template.id}
                  >
                    {template.name}{" "}
                    ({template.language})
                  </option>
                )
              )}

            </select>

          </div>

        </div>

        {/* SUMMARY */}

        <div className="new-campaign-info">

          <div className="new-campaign-info-icon">
            <Plus size={16} />
          </div>

          <div>
            <strong>
              Campaign starts as DRAFT
            </strong>

            <span>
              No messages will be sent when
              creating the campaign.
            </span>
          </div>

        </div>

        {/* ACTIONS */}

        <div className="new-campaign-actions">

          <button
            type="button"
            className="secondary-button"
            onClick={onCancel}
            disabled={submitting}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-button"
            disabled={submitting}
          >

            {submitting ? (
              <>
                <RefreshCw
                  size={16}
                  className="spin"
                />

                Creating...
              </>
            ) : (
              <>
                <Plus size={16} />

                Create Campaign
              </>
            )}

          </button>

        </div>

      </form>

    </div>
  );
}