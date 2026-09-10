import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  CheckCircle2,
  Clock3,
  FileText,
  Filter,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";

import { getTemplates, syncTemplates } from "../../api/templates";
import type { WhatsAppTemplate } from "../../types/template";
import useDashboardWebSocket, {
  type DashboardEvent,
} from "../../hooks/useDashboardWebSocket";

interface TemplatesPageProps {
  selectedTemplate: WhatsAppTemplate | null;
  onTemplateSelected: (template: WhatsAppTemplate | null) => void;
}

function statusClass(status: string) {
  return `template-status template-status-${status.toLowerCase()}`;
}

function StatusIcon({ status }: { status: string }) {
  if (status === "APPROVED") return <CheckCircle2 size={13} />;
  if (status === "REJECTED" || status === "DISABLED") return <XCircle size={13} />;
  if (status === "PENDING" || status === "PAUSED") return <Clock3 size={13} />;
  return <ShieldCheck size={13} />;
}

export default function TemplatesPage({
  selectedTemplate,
  onTemplateSelected,
}: TemplatesPageProps) {
  const [templates, setTemplates] = useState<WhatsAppTemplate[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const selectedTemplateIdRef = useRef<number | null>(selectedTemplate?.id ?? null);
  selectedTemplateIdRef.current = selectedTemplate?.id ?? null;

  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const result = await getTemplates({
        search: search.trim() || undefined,
        category: category || undefined,
        status: status || undefined,
        language: language || undefined,
      });
      setTemplates(result.templates);
      setLanguages(result.languages);

      if (result.templates.length === 0) {
        onTemplateSelected(null);
        return;
      }

      const currentId = selectedTemplateIdRef.current;
      const next = result.templates.find((item) => item.id === currentId) ?? result.templates[0];
      if (next.id !== currentId) {
        onTemplateSelected(next);
      }
    } catch (err) {
      console.error("Failed to load templates:", err);
      setError("Unable to load templates.");
    } finally {
      setLoading(false);
    }
  }, [category, language, onTemplateSelected, search, status]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadTemplates(), 220);
    return () => window.clearTimeout(timer);
  }, [loadTemplates]);

  const handleDashboardEvent = useCallback(
    (event: DashboardEvent) => {
      if (event.type === "template.created" || event.type === "template.updated") {
        const incoming = event.template as WhatsAppTemplate | undefined;
        if (!incoming) return;

        setTemplates((current) => {
          const exists = current.some((item) => item.id === incoming.id);
          if (exists) {
            return current.map((item) => item.id === incoming.id ? incoming : item);
          }
          return [incoming, ...current];
        });

        if (selectedTemplate?.id === incoming.id) {
          onTemplateSelected(incoming);
        }
        return;
      }

      if (event.type === "template.sync.completed") {
        setMessage("Templates synchronized with Meta.");
        void loadTemplates();
      }
    },
    [loadTemplates, onTemplateSelected, selectedTemplate?.id],
  );

  useDashboardWebSocket({ onEvent: handleDashboardEvent });

  const visibleCount = templates.length;

  const handleSync = async () => {
    try {
      setSyncing(true);
      setError("");
      setMessage("");
      const result = await syncTemplates();
      setMessage(
        `Sync complete · ${result.total} received · ${result.created} created · ${result.updated} updated`,
      );
      await loadTemplates();
    } catch (err) {
      console.error("Failed to sync templates:", err);
      setError("Template synchronization failed. Check the Meta API configuration and try again.");
    } finally {
      setSyncing(false);
    }
  };

  const summary = useMemo(() => {
    const approved = templates.filter((item) => item.status === "APPROVED").length;
    const pending = templates.filter((item) => item.status === "PENDING").length;
    const rejected = templates.filter((item) => item.status === "REJECTED").length;
    return { approved, pending, rejected };
  }, [templates]);

  return (
    <section className="templates-page">
      <div className="templates-toolbar">
        <div className="templates-search-wrap">
          <Search size={15} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search template name or Meta ID..."
          />
          {search && (
            <button type="button" className="templates-clear" onClick={() => setSearch("")} aria-label="Clear search">
              ×
            </button>
          )}
        </div>

        <div className="templates-filter">
          <Filter size={13} />
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All categories</option>
            <option value="MARKETING">Marketing</option>
            <option value="UTILITY">Utility</option>
            <option value="AUTHENTICATION">Authentication</option>
          </select>
        </div>

        <select className="templates-filter-select" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          <option value="APPROVED">Approved</option>
          <option value="PENDING">Pending</option>
          <option value="REJECTED">Rejected</option>
          <option value="PAUSED">Paused</option>
          <option value="DISABLED">Disabled</option>
        </select>

        <select className="templates-filter-select" value={language} onChange={(event) => setLanguage(event.target.value)}>
          <option value="">All languages</option>
          {languages.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>

        <button type="button" className="templates-sync-button" onClick={handleSync} disabled={syncing}>
          <RefreshCw size={14} className={syncing ? "templates-spin" : ""} />
          {syncing ? "Syncing..." : "Sync Meta"}
        </button>
      </div>

      <div className="templates-summary-row">
        <div><strong>{visibleCount}</strong><span>Visible</span></div>
        <div><strong>{summary.approved}</strong><span>Approved</span></div>
        <div><strong>{summary.pending}</strong><span>Pending</span></div>
        <div><strong>{summary.rejected}</strong><span>Rejected</span></div>
      </div>

      {message && <div className="templates-feedback templates-feedback-success">{message}</div>}
      {error && <div className="templates-feedback templates-feedback-error">{error}</div>}

      <div className="templates-table-card">
        <div className="templates-table-head">
          <div>Template</div>
          <div>Category</div>
          <div>Language</div>
          <div>Status</div>
          <div>Last synced</div>
        </div>

        {loading ? (
          <div className="templates-empty"><RefreshCw size={18} className="templates-spin" /><span>Loading templates...</span></div>
        ) : templates.length === 0 ? (
          <div className="templates-empty">
            <FileText size={28} />
            <strong>No templates found</strong>
            <span>Sync with Meta or adjust your filters.</span>
          </div>
        ) : (
          <div className="templates-table-body">
            {templates.map((template) => (
              <button
                type="button"
                key={template.id}
                className={`template-row ${selectedTemplate?.id === template.id ? "is-selected" : ""}`}
                onClick={() => onTemplateSelected(template)}
              >
                <div className="template-name-cell">
                  <span className="template-file-icon"><FileText size={15} /></span>
                  <span>
                    <strong>{template.name}</strong>
                    <small>{template.meta_template_id || `Local ID #${template.id}`}</small>
                  </span>
                </div>
                <div>{template.category}</div>
                <div><span className="template-language">{template.language}</span></div>
                <div><span className={statusClass(template.status)}><StatusIcon status={template.status} />{template.status}</span></div>
                <div className="template-date-cell">{template.synced_at ? new Date(template.synced_at).toLocaleString() : "—"}</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
