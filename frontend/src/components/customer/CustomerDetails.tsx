import {
  useEffect,
  useState,
} from "react";

import {
  MessageCircle,
  Pencil,
  Phone,
  CheckCircle2,
  XCircle,
  X,
  User,
  Smartphone,
  RefreshCw,
  Save,
} from "lucide-react";

import {
  updateCustomer,
} from "../../api/customers";

import type {
  Customer,
} from "../../types/customer";

// =========================================================
// PROPS
// =========================================================

interface CustomerDetailsProps {
  customer:
    | Customer
    | null;

  onOpenChat?: (
    customer: Customer,
  ) => void;

  onCustomerUpdated?: (
    customer: Customer,
  ) => void;
}

// =========================================================
// COMPONENT
// =========================================================

export default function CustomerDetails({
  customer,
  onOpenChat,
  onCustomerUpdated,
}: CustomerDetailsProps) {
  // =======================================================
  // EDIT STATE
  // =======================================================

  const [
    editing,
    setEditing,
  ] = useState(false);

  const [
    saving,
    setSaving,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    editName,
    setEditName,
  ] = useState("");

  const [
    editPhone,
    setEditPhone,
  ] = useState("");

  const [
    editWhatsappId,
    setEditWhatsappId,
  ] = useState("");

  const [
    editMarketingOptedIn,
    setEditMarketingOptedIn,
  ] = useState(false);

  const [
    editActive,
    setEditActive,
  ] = useState(true);

  const [
    editStatus,
    setEditStatus,
  ] = useState("");

  const [
    editTags,
    setEditTags,
  ] = useState("");

  // =======================================================
  // SYNC FORM WHEN CUSTOMER CHANGES
  // =======================================================

  useEffect(() => {
    if (!customer) {
      setEditing(false);
      return;
    }

    setEditName(
      customer.name || "",
    );

    setEditPhone(
      customer.phone || "",
    );

    setEditWhatsappId(
      customer.whatsapp_id ||
        "",
    );

    setEditMarketingOptedIn(
      customer.marketing_opted_in,
    );

    setEditActive(
      customer.is_active,
    );

    setEditStatus(
      customer.status || "",
    );

    setEditTags(
      customer.tags.join(", "),
    );

    setError(null);
  }, [customer]);

  // =======================================================
  // NO CUSTOMER
  // =======================================================

  if (!customer) {
    return (
      <div className="customer-details empty">

        <div className="customer-details-empty-icon">
          <User
            size={28}
          />
        </div>

        <h3>
          Select a customer
        </h3>

        <p>
          Select a customer from
          the list to view their
          details.
        </p>

      </div>
    );
  }

  // =======================================================
  // INITIALS
  // =======================================================

  const initials = (
    customer.name ||
    customer.phone ||
    "?"
  )
    .charAt(0)
    .toUpperCase();

  // =======================================================
  // OPEN EDIT
  // =======================================================

  const handleEdit =
    () => {
      setError(null);

      setEditName(
        customer.name || "",
      );

      setEditPhone(
        customer.phone || "",
      );

      setEditWhatsappId(
        customer.whatsapp_id ||
          "",
      );

      setEditMarketingOptedIn(
        customer.marketing_opted_in,
      );

      setEditActive(
        customer.is_active,
      );

      setEditStatus(
        customer.status || "",
      );

      setEditTags(
        customer.tags.join(", "),
      );

      setEditing(true);
    };

  // =======================================================
  // CANCEL EDIT
  // =======================================================

  const handleCancelEdit =
    () => {
      if (saving) {
        return;
      }

      setEditing(false);
      setError(null);
    };

  // =======================================================
  // SAVE EDIT
  // =======================================================

  const handleSave =
    async () => {
      const name =
        editName.trim();

      const phone =
        editPhone.trim();

      if (!name) {
        setError(
          "Customer name is required.",
        );
        return;
      }

      if (!phone) {
        setError(
          "Phone number is required.",
        );
        return;
      }

      try {
        setSaving(true);
        setError(null);

        const tags =
          editTags
            .split(",")
            .map(
              (tag) =>
                tag.trim(),
            )
            .filter(Boolean);

        const updated =
          await updateCustomer(
            customer.id,
            {
              name,
              phone,
              whatsapp_id:
                editWhatsappId.trim() ||
                null,
              marketing_opted_in:
                editMarketingOptedIn,
              is_active:
                editActive,
              status:
                editStatus.trim() ||
                customer.status,
              tags,
            },
          );

        onCustomerUpdated?.(
          updated,
        );

        setEditing(false);
      } catch (err: any) {
        console.error(
          "Unable to update customer:",
          err,
        );

        const message =
          err?.response?.data
            ?.error?.message ??
          err?.response?.data
            ?.message ??
          err?.message ??
          "Unable to update customer.";

        setError(message);
      } finally {
        setSaving(false);
      }
    };

  // =======================================================
  // EDIT MODE
  // =======================================================

  if (editing) {
    return (
      <div className="customer-details customer-details-edit">

        {/* Header */}

        <div className="customer-details-edit-header">

          <div>
            <h3>
              Edit Customer
            </h3>

            <p>
              Update customer
              information.
            </p>
          </div>

          <button
            type="button"
            className="customer-details-close"
            onClick={
              handleCancelEdit
            }
            disabled={saving}
          >
            <X
              size={18}
            />
          </button>

        </div>

        {/* Error */}

        {error && (
          <div className="customer-detail-error">
            {error}
          </div>
        )}

        {/* Form */}

        <div className="customer-edit-form">

          <div className="customer-form-group">

            <label>
              Customer Name
            </label>

            <div className="customer-form-input">

              <User
                size={15}
              />

              <input
                type="text"
                value={editName}
                onChange={(
                  event,
                ) =>
                  setEditName(
                    event.target
                      .value,
                  )
                }
              />

            </div>

          </div>

          <div className="customer-form-group">

            <label>
              Phone Number
            </label>

            <div className="customer-form-input">

              <Phone
                size={15}
              />

              <input
                type="text"
                value={editPhone}
                onChange={(
                  event,
                ) =>
                  setEditPhone(
                    event.target
                      .value,
                  )
                }
              />

            </div>

          </div>

          <div className="customer-form-group">

            <label>
              WhatsApp ID
            </label>

            <div className="customer-form-input">

              <Smartphone
                size={15}
              />

              <input
                type="text"
                value={
                  editWhatsappId
                }
                onChange={(
                  event,
                ) =>
                  setEditWhatsappId(
                    event.target
                      .value,
                  )
                }
              />

            </div>

          </div>

          <div className="customer-form-group">

            <label>
              Customer Status
            </label>

            <div className="customer-form-input">

              <User
                size={15}
              />

              <select
                value={
                  editStatus
                }
                onChange={(
                  event,
                ) =>
                  setEditStatus(
                    event.target
                      .value,
                  )
                }
              >
                <option value="active">
                  Active
                </option>

                <option value="inactive">
                  Inactive
                </option>

                <option value="new">
                  New
                </option>

                <option value="lead">
                  Lead
                </option>

                <option value="customer">
                  Customer
                </option>
              </select>

            </div>

          </div>

          <div className="customer-form-group">

            <label>
              Tags
            </label>

            <div className="customer-form-input">

              <input
                type="text"
                value={
                  editTags
                }
                onChange={(
                  event,
                ) =>
                  setEditTags(
                    event.target
                      .value,
                  )
                }
                placeholder="VIP, retail, lead"
              />

            </div>

            <small className="customer-form-help">
              Separate tags with
              commas.
            </small>

          </div>

          <label className="customer-checkbox-row">

            <input
              type="checkbox"
              checked={
                editMarketingOptedIn
              }
              onChange={(
                event,
              ) =>
                setEditMarketingOptedIn(
                  event.target
                    .checked,
                )
              }
            />

            <span>
              Marketing opt-in
            </span>

          </label>

          <label className="customer-checkbox-row">

            <input
              type="checkbox"
              checked={
                editActive
              }
              onChange={(
                event,
              ) =>
                setEditActive(
                  event.target
                    .checked,
                )
              }
            />

            <span>
              Customer is active
            </span>

          </label>

        </div>

        {/* Actions */}

        <div className="customer-details-edit-actions">

          <button
            type="button"
            className="secondary-button"
            onClick={
              handleCancelEdit
            }
            disabled={saving}
          >
            Cancel
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={
              handleSave
            }
            disabled={saving}
          >
            {saving ? (
              <>
                <RefreshCw
                  size={15}
                  className="spin"
                />

                Saving...
              </>
            ) : (
              <>
                <Save
                  size={15}
                />

                Save Changes
              </>
            )}
          </button>

        </div>

      </div>
    );
  }

  // =======================================================
  // NORMAL DETAILS VIEW
  // =======================================================

  return (
    <div className="customer-details">

      {/* =================================================
          PROFILE
          ================================================= */}

      <div className="customer-profile">

        <div className="customer-profile-avatar">
          {initials}
        </div>

        <h3>
          {customer.name ||
            "Unnamed Customer"}
        </h3>

        <p>
          {customer.phone}
        </p>

        <span
          className={`customer-status ${
            customer.is_active
              ? "active"
              : "inactive"
          }`}
        >
          <span className="customer-status-dot" />

          {customer.is_active
            ? "Active"
            : "Inactive"}
        </span>

      </div>

      {/* =================================================
          ACTIONS
          ================================================= */}

      <div className="customer-detail-actions">

        <button
          type="button"
          className="primary-button"
          onClick={() =>
            onOpenChat?.(
              customer,
            )
          }
        >
          <MessageCircle
            size={16}
          />

          Open Chat
        </button>

        <button
          type="button"
          className="secondary-button"
          onClick={
            handleEdit
          }
        >
          <Pencil
            size={16}
          />

          Edit
        </button>

      </div>

      {/* =================================================
          WHATSAPP
          ================================================= */}

      <div className="customer-detail-section">

        <div className="customer-detail-label">
          WhatsApp
        </div>

        <div className="customer-detail-row">

          <div className="customer-detail-icon">
            <Phone
              size={15}
            />
          </div>

          <div>
            <span className="customer-detail-value">
              {customer.whatsapp_id ||
                customer.phone}
            </span>

            <small>
              WhatsApp ID
            </small>
          </div>

        </div>

      </div>

      {/* =================================================
          MARKETING
          ================================================= */}

      <div className="customer-detail-section">

        <div className="customer-detail-label">
          Marketing Consent
        </div>

        <div className="customer-consent">

          {customer.marketing_opted_in ? (
            <>
              <CheckCircle2
                size={17}
              />

              <div>

                <strong>
                  Opted in
                </strong>

                {customer.marketing_opted_in_at && (
                  <small>
                    {formatDate(
                      customer.marketing_opted_in_at,
                    )}
                  </small>
                )}

              </div>
            </>
          ) : (
            <>
              <XCircle
                size={17}
              />

              <div>

                <strong>
                  Not opted in
                </strong>

                {customer.marketing_opted_out_at && (
                  <small>
                    {formatDate(
                      customer.marketing_opted_out_at,
                    )}
                  </small>
                )}

              </div>
            </>
          )}

        </div>

      </div>

      {/* =================================================
          TAGS
          ================================================= */}

      <div className="customer-detail-section">

        <div className="customer-detail-label">
          Tags
        </div>

        {customer.tags.length ===
        0 ? (
          <span className="customer-muted">
            No tags
          </span>
        ) : (
          <div className="customer-tags">

            {customer.tags.map(
              (
                tag,
                index,
              ) => (
                <span
                  key={`${tag}-${index}`}
                  className="customer-tag"
                >
                  {tag}
                </span>
              ),
            )}

          </div>
        )}

      </div>

      {/* =================================================
          ACTIVITY
          ================================================= */}

      <div className="customer-detail-section">

        <div className="customer-detail-label">
          Last Activity
        </div>

        <span className="customer-detail-value">
          {customer.last_message_at
            ? formatDate(
                customer.last_message_at,
              )
            : "No messages yet"}
        </span>

      </div>

      {/* =================================================
          STATUS
          ================================================= */}

      <div className="customer-detail-section">

        <div className="customer-detail-label">
          Customer Status
        </div>

        <span className="customer-status-value">
          {customer.status}
        </span>

      </div>

      {/* =================================================
          CUSTOMER ID
          ================================================= */}

      <div className="customer-detail-section">

        <div className="customer-detail-label">
          Customer ID
        </div>

        <span className="customer-detail-value">
          #{customer.id}
        </span>

      </div>

    </div>
  );
}

// =========================================================
// DATE FORMAT
// =========================================================

function formatDate(
  value: string,
): string {
  return new Date(
    value,
  ).toLocaleString();
}