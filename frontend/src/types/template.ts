export type TemplateCategory =
  | "AUTHENTICATION"
  | "MARKETING"
  | "UTILITY"
  | string;

export type TemplateStatus =
  | "APPROVED"
  | "PENDING"
  | "REJECTED"
  | "PAUSED"
  | "DISABLED"
  | "UNKNOWN"
  | string;

export interface WhatsAppTemplate {
  id: number;
  name: string;
  language: string;
  category: TemplateCategory;
  status: TemplateStatus;
  meta_template_id: string;
  components: Array<Record<string, unknown>>;
  quality_score: Record<string, unknown>;
  rejected_reason: string;
  synced_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TemplatesResponse {
  success: boolean;
  data: WhatsAppTemplate[];
  message: string;
  meta: {
    total: number;
    languages: string[];
  };
}

export interface TemplateResponse {
  success: boolean;
  data: WhatsAppTemplate;
  message: string;
  meta: Record<string, unknown>;
}

export interface TemplateSyncResult {
  total: number;
  created: number;
  updated: number;
}

export interface TemplateSyncResponse {
  success: boolean;
  data: TemplateSyncResult;
  message: string;
  meta: Record<string, unknown>;
}
