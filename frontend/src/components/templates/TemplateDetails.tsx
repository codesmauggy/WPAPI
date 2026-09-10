import {
  CheckCircle2,
  Clock3,
  FileText,
  Info,
  XCircle,
} from "lucide-react";
import type { WhatsAppTemplate } from "../../types/template";

interface TemplateDetailsProps {
  template: WhatsAppTemplate | null;
}

function statusClass(status: string) {
  return `template-status template-status-${status.toLowerCase()}`;
}

function renderText(text: string) {
  const parts = text.split(/(\{\{\d+\}\})/g);
  return parts.map((part, index) =>
    /^\{\{\d+\}\}$/.test(part)
      ? <mark key={`${part}-${index}`}>{part}</mark>
      : <span key={`${part}-${index}`}>{part}</span>,
  );
}

function componentType(component: Record<string, unknown>) {
  return String(component.type ?? "").toUpperCase();
}

function qualityText(score: Record<string, unknown>) {
  if (!score || Object.keys(score).length === 0) return "Not available";
  const value = score.score ?? score.status ?? score.quality_score;
  return value == null ? "Available" : String(value);
}

export default function TemplateDetails({ template }: TemplateDetailsProps) {
  if (!template) {
    return (
      <aside className="template-details-empty">
        <FileText size={26} />
        <strong>Select a template</strong>
        <span>Template details and a WhatsApp-style preview will appear here.</span>
      </aside>
    );
  }

  const header = template.components.find((item) => componentType(item) === "HEADER");
  const body = template.components.find((item) => componentType(item) === "BODY");
  const footer = template.components.find((item) => componentType(item) === "FOOTER");
  const buttons = template.components.find((item) => componentType(item) === "BUTTONS");

  const headerFormat = String(header?.format ?? "").toUpperCase();
  const headerText = typeof header?.text === "string" ? header.text : "";
  const bodyText = typeof body?.text === "string" ? body.text : "";
  const footerText = typeof footer?.text === "string" ? footer.text : "";
  const buttonItems = Array.isArray(buttons?.buttons) ? buttons.buttons : [];

  return (
    <aside className="template-details-panel">
      <div className="template-detail-hero">
        <div className="template-detail-icon"><FileText size={19} /></div>
        <div className="template-detail-title">
          <h3>{template.name}</h3>
          <span>{template.language} · {template.category}</span>
        </div>
        <span className={statusClass(template.status)}>{template.status}</span>
      </div>

      <div className="template-detail-stats">
        <div><span>Meta ID</span><strong>{template.meta_template_id || "—"}</strong></div>
        <div><span>Quality</span><strong>{qualityText(template.quality_score)}</strong></div>
      </div>

      {template.rejected_reason && (
        <div className="template-rejection"><XCircle size={14} /><div><strong>Rejection reason</strong><span>{template.rejected_reason}</span></div></div>
      )}

      <div className="template-section-title">WhatsApp Preview</div>
      <div className="template-preview-shell">
        <div className="template-preview-card">
          {header && (
            <div className={`template-preview-header ${headerFormat === "TEXT" ? "" : "is-media"}`}>
              {headerFormat === "TEXT" && headerText ? renderText(headerText) : headerFormat || "HEADER"}
            </div>
          )}
          <div className="template-preview-body">
            {bodyText ? renderText(bodyText) : <span className="template-preview-muted">No body content</span>}
          </div>
          {footerText && <div className="template-preview-footer">{renderText(footerText)}</div>}
          {buttonItems.length > 0 && (
            <div className="template-preview-buttons">
              {buttonItems.map((button, index) => {
                const item = button as Record<string, unknown>;
                return <button type="button" key={`${String(item.text ?? "button")}-${index}`}>{String(item.text ?? item.type ?? "Button")}</button>;
              })}
            </div>
          )}
        </div>
      </div>

      <div className="template-section-title">Components</div>
      <div className="template-components-list">
        {template.components.length === 0 ? (
          <div className="template-component-empty"><Info size={13} /> No components stored.</div>
        ) : template.components.map((component, index) => {
          const type = componentType(component) || "UNKNOWN";
          const text = typeof component.text === "string" ? component.text : "";
          return (
            <div className="template-component-item" key={`${type}-${index}`}>
              <div><strong>{type}</strong><span>{text || `${type.toLowerCase()} component`}</span></div>
            </div>
          );
        })}
      </div>

      <div className="template-detail-meta">
        <div><span>Created</span><strong>{template.created_at ? new Date(template.created_at).toLocaleString() : "—"}</strong></div>
        <div><span>Updated</span><strong>{template.updated_at ? new Date(template.updated_at).toLocaleString() : "—"}</strong></div>
        <div><span>Synced</span><strong>{template.synced_at ? new Date(template.synced_at).toLocaleString() : "—"}</strong></div>
      </div>
    </aside>
  );
}
