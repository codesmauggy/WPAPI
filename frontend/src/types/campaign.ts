export type CampaignStatus =
  | "DRAFT"
  | "SCHEDULED"
  | "RUNNING"
  | "PAUSED"
  | "COMPLETED"
  | "CANCELLED"
  | "FAILED";

export interface CampaignStatistics {
  total: number;
  pending: number;
  sending: number;
  sent: number;
  delivered: number;
  read: number;
  failed: number;
  cancelled: number;
  completed: number;
}

export interface CampaignAudience {
  id: number;
  name: string;
}

export interface CampaignTemplate {
  id: number;
  name: string;
  language?: string;
  status?: string;
}

export interface CampaignPhoneNumber {
  id: number;
  display_phone_number: string;
}

export interface Campaign {
  id: number;
  name: string;
  status: CampaignStatus;

  audience?: CampaignAudience | null;
  template?: CampaignTemplate | null;
  phone_number?: CampaignPhoneNumber | null;

  statistics: CampaignStatistics;

  created_at?: string;
  updated_at?: string;
  started_at?: string | null;
  completed_at?: string | null;
}