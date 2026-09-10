import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Check,
  CheckCircle2,
  FileText,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  Upload,
  UserPlus,
  Users,
  X,
  XCircle,
} from "lucide-react";

import {
  addAudienceMembersBulk,
  deleteAudience,
  getAudienceCustomers,
  getAudienceMembers,
  importAudienceCsv,
  removeAudienceMember,
  updateAudience,
} from "../../api/audience";
import type { Audience, AudienceMember } from "../../types/audience";
import type { Customer } from "../../types/customer";

interface AudienceDetailsProps {
  audience: Audience | null;
  onAudienceUpdated?: (audience: Audience) => void;
  onAudienceDeleted?: (audienceId: number) => void;
}


type AddMembersTab = "customers" | "csv";

function downloadTextReport(report: string) {
  const blob = new Blob([report], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "audience-import-errors.txt";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function downloadCsvTemplate() {
  const csv = "Name,Number,Whatsappid\nExample Customer,919876543210,919876543210\n";
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "audience-import-template.csv";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export default function AudienceDetails({
  audience,
  onAudienceUpdated,
  onAudienceDeleted,
}: AudienceDetailsProps) {
  const [members, setMembers] = useState<AudienceMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [availableCustomers, setAvailableCustomers] = useState<Customer[]>([]);
  const [customersLoading, setCustomersLoading] = useState(false);
  const [customerSearch, setCustomerSearch] = useState("");
  const [memberSearch, setMemberSearch] = useState("");
  const [selectedCustomerIds, setSelectedCustomerIds] = useState<number[]>([]);
  const [selectedMemberCustomerIds, setSelectedMemberCustomerIds] = useState<number[]>([]);
  const [showMembersModal, setShowMembersModal] = useState(false);
  const [showAddMembers, setShowAddMembers] = useState(false);
  const [addMembersTab, setAddMembersTab] = useState<AddMembersTab>("customers");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvImporting, setCsvImporting] = useState(false);
  const [csvReport, setCsvReport] = useState("");
  const csvInputRef = useRef<HTMLInputElement | null>(null);
  const [showEditForm, setShowEditForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [memberCountOverride, setMemberCountOverride] = useState<number | null>(null);

  const displayedMemberCount =
    memberCountOverride ?? audience?.member_count ?? 0;

  const loadMembers = useCallback(async (): Promise<AudienceMember[]> => {
    if (!audience) return [];

    try {
      setMembersLoading(true);
      const data = await getAudienceMembers(audience.id);
      setMembers(data);
      setSelectedMemberCustomerIds((current) =>
        current.filter((customerId) =>
          data.some((member) => member.customer.id === customerId),
        ),
      );
      setMemberCountOverride(data.length);
      return data;
    } catch (err) {
      console.error("Failed to load audience members:", err);
      setError("Unable to load audience members.");
      return [];
    } finally {
      setMembersLoading(false);
    }
  }, [audience]);

  const loadAvailableCustomers = useCallback(async () => {
    if (!audience || !showAddMembers || addMembersTab !== "customers") return;

    try {
      setCustomersLoading(true);
      const data = await getAudienceCustomers(audience.id, {
        search: customerSearch.trim() || undefined,
        is_active: true,
        marketing_opted_in: true,
      });
      setAvailableCustomers(data);
    } catch (err) {
      console.error("Failed to load eligible customers:", err);
      setAvailableCustomers([]);
      setError("Unable to load eligible customers.");
    } finally {
      setCustomersLoading(false);
    }
  }, [audience, addMembersTab, customerSearch, showAddMembers]);

  useEffect(() => {
    setMembers([]);
    setAvailableCustomers([]);
    setSelectedCustomerIds([]);
    setSelectedMemberCustomerIds([]);
    setShowMembersModal(false);
    setShowAddMembers(false);
    setAddMembersTab("customers");
    setCsvFile(null);
    setCsvReport("");
    setShowEditForm(false);
    setCustomerSearch("");
    setMemberSearch("");
    setName(audience?.name ?? "");
    setDescription(audience?.description ?? "");
    setMemberCountOverride(null);
    setError("");
    setMessage("");
  }, [audience?.id]);

  useEffect(() => {
    if (!showAddMembers) return;

    const timer = window.setTimeout(() => {
      void loadAvailableCustomers();
    }, 250);

    return () => window.clearTimeout(timer);
  }, [loadAvailableCustomers, showAddMembers, addMembersTab]);

  useEffect(() => {
    if (!showMembersModal) return;

    void loadMembers();
  }, [loadMembers, showMembersModal]);

  const filteredMembers = useMemo(() => {
    const query = memberSearch.trim().toLowerCase();
    if (!query) return members;

    return members.filter((member) =>
      [
        member.customer.name,
        member.customer.phone,
        member.customer.whatsapp_id ?? "",
      ].some((value) => value.toLowerCase().includes(query)),
    );
  }, [memberSearch, members]);

  const selectedCount = selectedCustomerIds.length;

  const allVisibleMembersSelected = useMemo(
    () =>
      filteredMembers.length > 0 &&
      filteredMembers.every((member) =>
        selectedMemberCustomerIds.includes(member.customer.id),
      ),
    [filteredMembers, selectedMemberCustomerIds],
  );

  const allVisibleSelected = useMemo(
    () =>
      availableCustomers.length > 0 &&
      availableCustomers.every((customer) =>
        selectedCustomerIds.includes(customer.id),
      ),
    [availableCustomers, selectedCustomerIds],
  );

  if (!audience) {
    return (
      <div className="audience-ops-empty">
        <div className="audience-ops-empty-icon">
          <Users size={22} />
        </div>
        <strong>Select an audience</strong>
        <span>Select an audience from the list to manage it.</span>
      </div>
    );
  }

  const handleUpdate = async () => {
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Audience name is required.");
      return;
    }

    try {
      setSaving(true);
      setError("");
      const updated = await updateAudience(audience.id, {
        name: trimmedName,
        description: description.trim(),
      });
      onAudienceUpdated?.(updated);
      setShowEditForm(false);
      setMessage("Audience updated successfully.");
    } catch (err) {
      console.error("Failed to update audience:", err);
      setError("Unable to update audience.");
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async () => {
    try {
      setSaving(true);
      setError("");
      const updated = await updateAudience(audience.id, {
        is_active: !audience.is_active,
      });
      onAudienceUpdated?.(updated);
      setMessage(updated.is_active ? "Audience activated." : "Audience deactivated.");
    } catch (err) {
      console.error("Failed to change audience status:", err);
      setError("Unable to change audience status.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    const confirmed = window.confirm(`Delete audience "${audience.name}"?`);
    if (!confirmed) return;

    try {
      setSaving(true);
      setError("");
      await deleteAudience(audience.id);
      onAudienceDeleted?.(audience.id);
    } catch (err) {
      console.error("Failed to delete audience:", err);
      setError("Unable to delete audience. It may be used by a campaign.");
    } finally {
      setSaving(false);
    }
  };

  const openMembersModal = () => {
    setError("");
    setMessage("");
    setSelectedMemberCustomerIds([]);
    setShowMembersModal(true);
  };

  const openAddMembersModal = () => {
    setError("");
    setMessage("");
    setCustomerSearch("");
    setSelectedCustomerIds([]);
    setCsvFile(null);
    setCsvReport("");
    setAddMembersTab("customers");
    setShowAddMembers(true);
  };

  const closeAddMembers = () => {
    if (csvImporting || saving) return;
    setShowAddMembers(false);
    setCustomerSearch("");
    setSelectedCustomerIds([]);
    setAvailableCustomers([]);
    setCsvFile(null);
    setCsvReport("");
    setAddMembersTab("customers");
    if (csvInputRef.current) csvInputRef.current.value = "";
  };

  const toggleMember = (customerId: number) => {
    setSelectedMemberCustomerIds((current) =>
      current.includes(customerId)
        ? current.filter((id) => id !== customerId)
        : [...current, customerId],
    );
  };

  const toggleAllVisibleMembers = () => {
    const visibleIds = filteredMembers.map((member) => member.customer.id);

    setSelectedMemberCustomerIds((current) => {
      if (allVisibleMembersSelected) {
        return current.filter((id) => !visibleIds.includes(id));
      }
      return Array.from(new Set([...current, ...visibleIds]));
    });
  };

  const handleRemoveSelectedMembers = async () => {
    const ids = [...selectedMemberCustomerIds];
    if (!ids.length) return;

    const confirmed = window.confirm(
      `Remove ${ids.length} selected member${ids.length === 1 ? "" : "s"} from "${audience.name}"?`,
    );
    if (!confirmed) return;

    try {
      setSaving(true);
      setError("");
      setMessage("");

      const results = await Promise.allSettled(
        ids.map((customerId) => removeAudienceMember(audience.id, customerId)),
      );

      const removedIds = ids.filter(
        (_, index) => results[index]?.status === "fulfilled",
      );
      const failed = ids.length - removedIds.length;

      if (removedIds.length) {
        const removedSet = new Set(removedIds);
        setMembers((current) =>
          current.filter((member) => !removedSet.has(member.customer.id)),
        );
        const newCount = Math.max(0, displayedMemberCount - removedIds.length);
        setMemberCountOverride(newCount);
        onAudienceUpdated?.({
          ...audience,
          member_count: newCount,
        });
      }

      setSelectedMemberCustomerIds((current) =>
        current.filter((id) => !removedIds.includes(id)),
      );

      if (failed) {
        setError(
          `${removedIds.length} member${removedIds.length === 1 ? "" : "s"} removed. ${failed} could not be removed.`,
        );
      } else {
        setMessage(
          `${removedIds.length} member${removedIds.length === 1 ? "" : "s"} removed successfully.`,
        );
      }
    } catch (err) {
      console.error("Failed to remove selected audience members:", err);
      setError("Unable to remove selected audience members.");
    } finally {
      setSaving(false);
    }
  };

  const toggleCustomer = (customerId: number) => {
    setSelectedCustomerIds((current) =>
      current.includes(customerId)
        ? current.filter((id) => id !== customerId)
        : [...current, customerId],
    );
  };

  const toggleAllVisible = () => {
    const visibleIds = availableCustomers.map((customer) => customer.id);

    setSelectedCustomerIds((current) => {
      if (allVisibleSelected) {
        return current.filter((id) => !visibleIds.includes(id));
      }
      return Array.from(new Set([...current, ...visibleIds]));
    });
  };

  const handleAddMembers = async () => {
    if (!selectedCustomerIds.length) return;

    try {
      setSaving(true);
      setError("");
      setMessage("");

      const result = await addAudienceMembersBulk(audience.id, {
        customer_ids: selectedCustomerIds,
      });

      const loadedMembers = await loadMembers();
      const newCount = loadedMembers.length || result.member_count;
      setMemberCountOverride(newCount);
      onAudienceUpdated?.({ ...audience, member_count: newCount });
      setSelectedCustomerIds([]);
      setAvailableCustomers([]);
      setCustomerSearch("");
      setShowAddMembers(false);

      if (result.already_members > 0) {
        setMessage(`${result.added} member${result.added === 1 ? "" : "s"} added. ${result.already_members} already ${result.already_members === 1 ? "was" : "were"} in this audience.`);
      } else {
        setMessage(`${result.added} member${result.added === 1 ? "" : "s"} added successfully.`);
      }
    } catch (err) {
      console.error("Failed to add audience members:", err);
      setError("Unable to add audience members. They may no longer be eligible.");
    } finally {
      setSaving(false);
    }
  };

  const handleCsvImport = async () => {
    if (!csvFile) {
      setError("Please select a CSV file first.");
      return;
    }

    try {
      setCsvImporting(true);
      setError("");
      setMessage("");
      setCsvReport("");

      const result = await importAudienceCsv(audience.id, csvFile);
      const loadedMembers = await loadMembers();
      const newCount = loadedMembers.length;
      setMemberCountOverride(newCount);
      onAudienceUpdated?.({ ...audience, member_count: newCount });

      if (result.errors > 0 && result.report) {
        setCsvReport(result.report);
        downloadTextReport(result.report);
        setMessage(`CSV import completed: ${result.imported} imported, ${result.errors} error${result.errors === 1 ? "" : "s"}. The error report was downloaded.`);
      } else {
        setMessage(`CSV import completed: ${result.imported} member${result.imported === 1 ? "" : "s"} imported successfully.`);
      }

      setCsvFile(null);
      if (csvInputRef.current) csvInputRef.current.value = "";
    } catch (err) {
      console.error("Failed to import audience CSV:", err);
      setError("Unable to import CSV. Check the file format and try again.");
    } finally {
      setCsvImporting(false);
    }
  };

  const handleRemoveMember = async (customerId: number) => {
    try {
      setSaving(true);
      setError("");

      await removeAudienceMember(audience.id, customerId);

      setMembers((current) =>
        current.filter((member) => member.customer.id !== customerId),
      );
      const newCount = Math.max(0, displayedMemberCount - 1);
      setMemberCountOverride(newCount);
      onAudienceUpdated?.({
        ...audience,
        member_count: newCount,
      });
      setMessage("Member removed from audience.");
    } catch (err) {
      console.error("Failed to remove audience member:", err);
      setError("Unable to remove audience member.");
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (value: string | null) => {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleDateString(undefined, {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div className="audience-ops-panel">
      <section className="audience-ops-hero">
        <div className="audience-ops-avatar">
          <Users size={23} />
        </div>
        <div className="audience-ops-hero-copy">
          <h3 title={audience.name}>{audience.name}</h3>
          <span>Customer audience</span>
        </div>
        <span
          className={`audience-ops-status ${audience.is_active ? "active" : "inactive"}`}
        >
          <span />
          {audience.is_active ? "Active" : "Inactive"}
        </span>
      </section>

      {audience.description && (
        <section className="audience-ops-description">
          {audience.description}
        </section>
      )}

      <section className="audience-ops-stats">
        <div className="audience-ops-stat">
          <div className="audience-ops-stat-icon"><Users size={15} /></div>
          <div>
            <strong>{displayedMemberCount}</strong>
            <span>Members</span>
          </div>
        </div>
        <div className="audience-ops-stat">
          <div className="audience-ops-stat-icon"><CheckCircle2 size={15} /></div>
          <div>
            <strong>{audience.is_active ? "ON" : "OFF"}</strong>
            <span>Audience status</span>
          </div>
        </div>
      </section>

      <section className="audience-ops-card audience-ops-member-card">
        <div className="audience-ops-card-heading">
          <div className="audience-ops-card-icon"><Users size={16} /></div>
          <div>
            <h4>Audience Members</h4>
            <p>{displayedMemberCount} customer{displayedMemberCount === 1 ? "" : "s"} in this audience</p>
          </div>
        </div>

        <button
          className="audience-ops-view-members"
          type="button"
          onClick={openMembersModal}
        >
          <Users size={14} />
          View Members
        </button>

        <button
          className="audience-ops-add-members"
          type="button"
          onClick={openAddMembersModal}
          disabled={saving}
        >
          <UserPlus size={14} />
          Add Members
        </button>
      </section>

      <section className="audience-ops-card">
        <div className="audience-ops-card-title">Audience Controls</div>
        <div className="audience-ops-action-grid">
          <button
            className="audience-ops-action secondary"
            type="button"
            onClick={() => setShowEditForm(true)}
            disabled={saving}
          >
            <Pencil size={14} />
            <span>Edit</span>
          </button>
          <button
            className="audience-ops-action secondary"
            type="button"
            onClick={() => void handleToggleActive()}
            disabled={saving}
          >
            {audience.is_active ? <XCircle size={14} /> : <CheckCircle2 size={14} />}
            <span>{audience.is_active ? "Deactivate" : "Activate"}</span>
          </button>
          <button
            className="audience-ops-action danger"
            type="button"
            onClick={() => void handleDelete()}
            disabled={saving}
          >
            <Trash2 size={14} />
            <span>Delete</span>
          </button>
        </div>
      </section>

      <section className="audience-ops-meta">
        <div>
          <span>Audience ID</span>
          <strong>#{audience.id}</strong>
        </div>
        <div>
          <span>Created</span>
          <strong>{formatDate(audience.created_at)}</strong>
        </div>
        <div>
          <span>Last updated</span>
          <strong>{formatDate(audience.updated_at)}</strong>
        </div>
      </section>

      {(error || message) && (
        <div className={`audience-ops-alert ${error ? "error" : "success"}`}>
          {error || message}
        </div>
      )}

      {showEditForm && (
        <div className="audience-dialog-backdrop" onMouseDown={() => setShowEditForm(false)}>
          <div className="audience-dialog audience-dialog-small" onMouseDown={(event) => event.stopPropagation()}>
            <div className="audience-dialog-header">
              <div>
                <span className="audience-dialog-eyebrow">AUDIENCE SETTINGS</span>
                <h3>Edit Audience</h3>
              </div>
              <button className="audience-dialog-close" type="button" onClick={() => setShowEditForm(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="audience-dialog-body">
              <label className="audience-dialog-field">
                <span>Audience Name</span>
                <input value={name} onChange={(event) => setName(event.target.value)} />
              </label>
              <label className="audience-dialog-field">
                <span>Description</span>
                <textarea value={description} onChange={(event) => setDescription(event.target.value)} />
              </label>
            </div>
            <div className="audience-dialog-footer">
              <button className="secondary-button" type="button" onClick={() => setShowEditForm(false)}>Cancel</button>
              <button className="primary-button" type="button" onClick={() => void handleUpdate()} disabled={saving}>
                <Pencil size={13} /> {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showMembersModal && (
        <div className="audience-dialog-backdrop" onMouseDown={() => setShowMembersModal(false)}>
          <div className="audience-dialog audience-members-dialog" onMouseDown={(event) => event.stopPropagation()}>
            <div className="audience-dialog-header">
              <div className="audience-dialog-heading-with-icon">
                <div className="audience-dialog-main-icon"><Users size={18} /></div>
                <div>
                  <span className="audience-dialog-eyebrow">AUDIENCE MEMBERS</span>
                  <h3>{audience.name}</h3>
                  <p>{displayedMemberCount} member{displayedMemberCount === 1 ? "" : "s"}</p>
                </div>
              </div>
              <button className="audience-dialog-close" type="button" onClick={() => setShowMembersModal(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="audience-members-toolbar">
              <label className="audience-members-select-all">
                <input
                  type="checkbox"
                  checked={allVisibleMembersSelected}
                  onChange={toggleAllVisibleMembers}
                  disabled={membersLoading || filteredMembers.length === 0}
                />
                <span>Select all</span>
              </label>
              <div className="audience-dialog-search">
                <Search size={15} />
                <input
                  value={memberSearch}
                  onChange={(event) => setMemberSearch(event.target.value)}
                  placeholder="Search members..."
                />
              </div>
              <span className="audience-members-selection-count">
                {selectedMemberCustomerIds.length} selected
              </span>
              {selectedMemberCustomerIds.length > 0 && (
                <button
                  className="audience-dialog-bulk-delete"
                  type="button"
                  onClick={() => void handleRemoveSelectedMembers()}
                  disabled={saving || membersLoading}
                >
                  <Trash2 size={14} />
                  Delete Selected
                </button>
              )}
              <button
                className="audience-dialog-refresh"
                type="button"
                title="Refresh members"
                onClick={() => void loadMembers()}
                disabled={membersLoading || saving}
              >
                <RefreshCw size={15} className={membersLoading ? "spin" : undefined} />
              </button>
              <button className="primary-button" type="button" onClick={openAddMembersModal} disabled={saving}>
                <UserPlus size={13} /> Add Members
              </button>
            </div>

            <div className="audience-members-dialog-list">
              {membersLoading ? (
                <div className="audience-dialog-empty">
                  <Loader2 size={20} className="spin" />
                  <span>Loading members...</span>
                </div>
              ) : members.length === 0 ? (
                <div className="audience-dialog-empty">
                  <Users size={24} />
                  <strong>No members yet</strong>
                  <span>Add customers to start building this audience.</span>
                </div>
              ) : (
                filteredMembers.map((member) => (
                  <div
                    key={member.id}
                    className={`audience-dialog-member-row ${
                      selectedMemberCustomerIds.includes(member.customer.id) ? "selected" : ""
                    }`}
                  >
                    <label className="audience-member-checkbox" title="Select member">
                      <input
                        type="checkbox"
                        checked={selectedMemberCustomerIds.includes(member.customer.id)}
                        onChange={() => toggleMember(member.customer.id)}
                        disabled={saving}
                      />
                    </label>
                    <div className="audience-dialog-member-avatar">
                      {member.customer.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="audience-dialog-member-info">
                      <strong>{member.customer.name}</strong>
                      <span>{member.customer.phone}</span>
                      {member.customer.whatsapp_id && (
                        <small>WA: {member.customer.whatsapp_id}</small>
                      )}
                    </div>
                    <span className={`audience-dialog-optin ${member.customer.marketing_opted_in ? "yes" : "no"}`}>
                      {member.customer.marketing_opted_in ? "Opted in" : "No opt-in"}
                    </span>
                    <button
                      className="audience-dialog-remove"
                      type="button"
                      title="Remove member"
                      onClick={() => void handleRemoveMember(member.customer.id)}
                      disabled={saving}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))
              )}
              {!membersLoading && members.length > 0 && filteredMembers.length === 0 && (
                <div className="audience-dialog-empty compact">
                  <Search size={20} />
                  <span>No members match your search.</span>
                </div>
              )}
            </div>

            <div className="audience-dialog-footer">
              <span className="audience-dialog-footer-note">Changes are saved immediately.</span>
              <button className="secondary-button" type="button" onClick={() => setShowMembersModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {showAddMembers && (
        <div
          className="audience-add-modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeAddMembers();
          }}
        >
          <div
            className="audience-add-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="audience-add-members-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="audience-add-modal-header">
              <div>
                <h3 id="audience-add-members-title">Add Members</h3>
                <p>Add eligible customers to <strong>{audience.name}</strong>.</p>
              </div>
              <button className="icon-button" type="button" onClick={closeAddMembers} disabled={csvImporting || saving} title="Close">
                <X size={18} />
              </button>
            </div>

            <div className="audience-add-modal-tabs">
              <button type="button" className={addMembersTab === "customers" ? "active" : ""} onClick={() => { setError(""); setAddMembersTab("customers"); }} disabled={csvImporting}>
                <Users size={14} /> Select Customers
              </button>
              <button type="button" className={addMembersTab === "csv" ? "active" : ""} onClick={() => { setError(""); setAddMembersTab("csv"); }} disabled={csvImporting}>
                <Upload size={14} /> Import CSV
              </button>
            </div>

            {addMembersTab === "customers" ? (
              <>
                <div className="audience-add-modal-body">
                  <div className="audience-search">
                    <Search size={14} />
                    <input value={customerSearch} onChange={(event) => setCustomerSearch(event.target.value)} placeholder="Search eligible customers..." autoFocus />
                  </div>
                  <div className="audience-eligibility-note">Showing active customers with marketing opt-in who are not already members.</div>
                  <div className="audience-select-all-row">
                    <label>
                      <input type="checkbox" checked={allVisibleSelected} onChange={toggleAllVisible} disabled={customersLoading || availableCustomers.length === 0} />
                      Select all visible
                    </label>
                    <span>{selectedCount} selected</span>
                  </div>
                  <div className="audience-customer-picker">
                    {customersLoading ? (
                      <div className="audience-members-loading"><Loader2 size={15} className="spin" /> Loading eligible customers...</div>
                    ) : availableCustomers.length === 0 ? (
                      <div className="audience-members-empty"><Users size={17} /> No eligible customers found.</div>
                    ) : (
                      availableCustomers.map((customer) => (
                        <label key={customer.id} className="audience-customer-option">
                          <input type="checkbox" checked={selectedCustomerIds.includes(customer.id)} onChange={() => toggleCustomer(customer.id)} />
                          <span className="audience-member-avatar">{customer.name.charAt(0).toUpperCase()}</span>
                          <span className="audience-member-info"><strong>{customer.name}</strong><span>{customer.phone}{customer.whatsapp_id ? ` • WA ${customer.whatsapp_id}` : ""}</span></span>
                          <span className="audience-optin yes">Opted in</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
                <div className="audience-add-modal-footer">
                  <button className="secondary-button" type="button" onClick={closeAddMembers} disabled={saving}>Cancel</button>
                  <button className="primary-button" type="button" onClick={() => void handleAddMembers()} disabled={!selectedCount || saving || customersLoading}>
                    {saving ? <Loader2 size={14} className="spin" /> : <Plus size={14} />}
                    {saving ? "Adding..." : `Add ${selectedCount} Member${selectedCount === 1 ? "" : "s"}`}
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="audience-add-modal-body">
                  <div className="audience-csv-intro">
                    <div className="audience-csv-icon"><FileText size={22} /></div>
                    <div><strong>Import customers from CSV</strong><span>Required columns: <b>Name</b>, <b>Number</b>, <b>Whatsappid</b>.</span></div>
                  </div>
                  <div className="audience-csv-rules">
                    <div><CheckCircle2 size={14} /> New customers are created with marketing opt-in enabled by default.</div>
                    <div><CheckCircle2 size={14} /> Existing customers are matched by Number or Whatsappid.</div>
                    <div><CheckCircle2 size={14} /> Existing consent is never overwritten.</div>
                    <div><CheckCircle2 size={14} /> Failed rows are returned in a TXT error report.</div>
                  </div>
                  <div className="audience-csv-file-picker">
                    <input ref={csvInputRef} type="file" accept=".csv,text/csv" onChange={(event) => { setCsvFile(event.target.files?.[0] ?? null); setCsvReport(""); setError(""); }} />
                    <button className="secondary-button" type="button" onClick={() => csvInputRef.current?.click()} disabled={csvImporting}><Upload size={14} /> Choose CSV</button>
                    <span>{csvFile ? csvFile.name : "No file selected"}</span>
                  </div>
                  <button className="audience-template-button" type="button" onClick={downloadCsvTemplate} disabled={csvImporting}><FileText size={13} /> Download CSV template</button>
                  {csvReport && (
                    <div className="audience-csv-report">
                      <div><strong>Import error report ready</strong><span>Failed rows are listed with the original values and error reason.</span></div>
                      <button className="secondary-button" type="button" onClick={() => downloadTextReport(csvReport)}><FileText size={13} /> Download Again</button>
                    </div>
                  )}
                </div>
                <div className="audience-add-modal-footer">
                  <button className="secondary-button" type="button" onClick={closeAddMembers} disabled={csvImporting}>Close</button>
                  <button className="primary-button" type="button" onClick={() => void handleCsvImport()} disabled={!csvFile || csvImporting}>
                    {csvImporting ? <Loader2 size={14} className="spin" /> : <Upload size={14} />}
                    {csvImporting ? "Importing..." : "Import CSV"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
