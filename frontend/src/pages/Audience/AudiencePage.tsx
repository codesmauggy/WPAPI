import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  Plus,
  RefreshCw,
  Search,
  Users,
  UsersRound,
  XCircle,
} from "lucide-react";

import { createAudience, getAudiences } from "../../api/audience";
import type { Audience } from "../../types/audience";
import useDashboardWebSocket, {
  type DashboardEvent,
} from "../../hooks/useDashboardWebSocket";

interface AudiencePageProps {
  selectedAudience?: Audience | null;
  initialAudienceId?: number | null;
  refreshToken?: number;
  onAudienceSelected?: (audience: Audience | null) => void;
}

export default function AudiencePage({
  selectedAudience,
  initialAudienceId = null,
  refreshToken = 0,
  onAudienceSelected,
}: AudiencePageProps) {
  const [audiences, setAudiences] = useState<Audience[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const selectedId = selectedAudience?.id ?? null;
  const selectedIdRef = useRef<number | null>(selectedId);
  selectedIdRef.current = selectedId;

  const loadAudiences = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getAudiences({
        search: search.trim() || undefined,
      });

      setAudiences(data);

      if (!data.length) {
        onAudienceSelected?.(null);
        return;
      }

      const preferredId = selectedIdRef.current ?? initialAudienceId;
      const selected =
        data.find((item) => item.id === preferredId) ?? data[0];

      if (selected.id !== selectedId) {
        onAudienceSelected?.(selected);
      }
    } catch (err) {
      console.error("Failed to load audiences:", err);
      setError("Unable to load audiences.");
    } finally {
      setLoading(false);
    }
  }, [initialAudienceId, onAudienceSelected, search]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadAudiences();
    }, 250);

    return () => window.clearTimeout(timer);
  }, [loadAudiences, refreshToken]);

  const handleDashboardEvent = useCallback(
    (event: DashboardEvent) => {
      if (event.type === "audience.created" && event.audience) {
        const incoming = event.audience as Audience;
        setAudiences((current) => {
          if (current.some((item) => item.id === incoming.id)) {
            return current.map((item) => item.id === incoming.id ? { ...item, ...incoming } : item);
          }
          return [incoming, ...current];
        });
        if (!selectedIdRef.current) onAudienceSelected?.(incoming);
        return;
      }

      if (event.type === "audience.updated" && event.audience) {
        const incoming = event.audience as Audience;
        setAudiences((current) => current.map((item) =>
          item.id === incoming.id ? { ...item, ...incoming } : item,
        ));
        if (selectedIdRef.current === incoming.id) onAudienceSelected?.(incoming);
        return;
      }

      if (event.type === "audience.membership.updated" && event.audience) {
        const incoming = event.audience as Audience;
        setAudiences((current) => current.map((item) =>
          item.id === incoming.id
            ? { ...item, member_count: incoming.member_count, updated_at: incoming.updated_at ?? item.updated_at }
            : item,
        ));
        if (selectedIdRef.current === incoming.id) {
          const selected = {
            ...(selectedAudience ?? incoming),
            member_count: incoming.member_count,
            updated_at: incoming.updated_at ?? selectedAudience?.updated_at ?? null,
          };
          onAudienceSelected?.(selected);
        }
        return;
      }

      if (event.type === "audience.deleted" && event.audience_id) {
        const deletedId = Number(event.audience_id);
        setAudiences((current) => current.filter((item) => item.id !== deletedId));
        if (selectedIdRef.current === deletedId) onAudienceSelected?.(null);
      }
    },
    [onAudienceSelected, selectedAudience],
  );

  useDashboardWebSocket({ onEvent: handleDashboardEvent });

  const handleSelectAudience = (audience: Audience) => {
    setActionMessage("");
    onAudienceSelected?.(audience);
  };

  const handleCreate = async () => {
    const trimmedName = name.trim();

    if (!trimmedName) {
      setError("Audience name is required.");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setActionMessage("");

      const created = await createAudience({
        name: trimmedName,
        description: description.trim(),
        is_active: true,
      });

      setAudiences((current) => [
        created,
        ...current.filter((item) => item.id !== created.id),
      ]);

      onAudienceSelected?.(created);
      setName("");
      setDescription("");
      setShowCreateForm(false);
      setActionMessage("Audience created successfully.");
    } catch (err) {
      console.error("Failed to create audience:", err);
      setError("Unable to create audience.");
    } finally {
      setSaving(false);
    }
  };

  const totalAudiences = audiences.length;
  const activeAudiences = audiences.filter((item) => item.is_active).length;
  const inactiveAudiences = totalAudiences - activeAudiences;
  const totalMembers = audiences.reduce(
    (total, item) => total + Number(item.member_count ?? 0),
    0,
  );

  const visibleAudiences = useMemo(() => audiences, [audiences]);

  return (
    <div className="audience-page">
      <div className="audience-page-header">
        <div>
          <h2>Audience</h2>
          <p>Manage customer groups for campaigns and messaging.</p>
        </div>

        <div className="audience-header-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => void loadAudiences()}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? "spin" : undefined} />
            Refresh
          </button>

          <button
            className="primary-button"
            type="button"
            onClick={() => {
              setName("");
              setDescription("");
              setError("");
              setActionMessage("");
              setShowCreateForm(true);
            }}
          >
            <Plus size={15} />
            Create Audience
          </button>
        </div>
      </div>

      <div className="audience-summary">
        <div className="audience-summary-card">
          <div className="audience-summary-icon"><Users size={18} /></div>
          <span>Total Audiences</span>
          <strong>{totalAudiences}</strong>
        </div>

        <div className="audience-summary-card">
          <div className="audience-summary-icon"><CheckCircle2 size={18} /></div>
          <span>Active</span>
          <strong>{activeAudiences}</strong>
        </div>

        <div className="audience-summary-card">
          <div className="audience-summary-icon"><XCircle size={18} /></div>
          <span>Inactive</span>
          <strong>{inactiveAudiences}</strong>
        </div>

        <div className="audience-summary-card">
          <div className="audience-summary-icon"><UsersRound size={18} /></div>
          <span>Total Members</span>
          <strong>{totalMembers}</strong>
        </div>
      </div>

      <div className="audience-toolbar">
        <div className="audience-search">
          <Search size={15} />
          <input
            type="text"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search audiences..."
          />
        </div>
      </div>

      {error && <div className="audience-message error">{error}</div>}
      {actionMessage && (
        <div className="audience-message success">{actionMessage}</div>
      )}

      {showCreateForm && (
        <div className="audience-form-card">
          <div className="audience-form-header">
            <div>
              <h3>Create Audience</h3>
              <p>Create a customer group for future campaigns.</p>
            </div>
            <button
              className="icon-button"
              type="button"
              onClick={() => setShowCreateForm(false)}
            >
              <XCircle size={17} />
            </button>
          </div>

          <div className="audience-form-grid">
            <div className="audience-form-group">
              <label>Audience Name</label>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="e.g. VIP Customers"
              />
            </div>

            <div className="audience-form-group">
              <label>Description</label>
              <input
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Optional description"
              />
            </div>
          </div>

          <div className="audience-form-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={() => setShowCreateForm(false)}
            >
              Cancel
            </button>
            <button
              className="primary-button"
              type="button"
              onClick={() => void handleCreate()}
              disabled={saving}
            >
              <Plus size={14} />
              {saving ? "Creating..." : "Create Audience"}
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="audience-loading">Loading audiences...</div>
      ) : visibleAudiences.length === 0 ? (
        <div className="audience-empty">
          <Users size={30} />
          <h3>No audiences found</h3>
          <p>Create your first audience to organize customers for campaigns.</p>
        </div>
      ) : (
        <div className="audience-list">
          {visibleAudiences.map((audience) => (
            <button
              key={audience.id}
              type="button"
              className={`audience-row ${selectedId === audience.id ? "selected" : ""}`}
              onClick={() => handleSelectAudience(audience)}
            >
              <div className="audience-avatar"><Users size={18} /></div>

              <div className="audience-info">
                <div className="audience-row-top">
                  <strong>{audience.name}</strong>
                  <span className={`audience-status ${audience.is_active ? "active" : "inactive"}`}>
                    <span className="audience-status-dot" />
                    {audience.is_active ? "Active" : "Inactive"}
                  </span>
                </div>

                <div className="audience-description">
                  {audience.description || "No description"}
                </div>

                <div className="audience-row-meta">
                  <span><Users size={11} /> {audience.member_count} members</span>
                  <span>ID #{audience.id}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
