import type { Customer } from "./customer";

// =========================================================
// AUDIENCE
// =========================================================

export interface Audience {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  member_count: number;
  created_at: string | null;
  updated_at: string | null;
}

// =========================================================
// AUDIENCE MEMBER
// =========================================================

export interface AudienceMember {
  id: number;
  audience_id: number;
  customer: Customer;
  created_at: string | null;
}

// =========================================================
// AUDIENCE RESPONSES
// =========================================================

export interface AudiencesResponse {
  success: boolean;
  data: Audience[];
  message: string;
  meta: {
    total: number;
  };
}

export interface AudienceResponse {
  success: boolean;
  data: Audience;
  message: string;
  meta: Record<string, unknown>;
}

// =========================================================
// AUDIENCE MEMBER RESPONSES
// =========================================================

export interface AudienceMembersResponse {
  success: boolean;
  data: AudienceMember[];
  message: string;
  meta: {
    total: number;
  };
}

export interface AudienceMemberResponse {
  success: boolean;
  data: AudienceMember;
  message: string;
  meta: Record<string, unknown>;
}

// =========================================================
// AUDIENCE CUSTOMER RESPONSE
// =========================================================

export interface AudienceCustomersResponse {
  success: boolean;
  data: Customer[];
  message: string;
  meta: {
    total: number;
  };
}

// =========================================================
// CREATE AUDIENCE
// =========================================================

export interface CreateAudiencePayload {
  name: string;
  description?: string;
  is_active?: boolean;
}

// =========================================================
// UPDATE AUDIENCE
// =========================================================

export interface UpdateAudiencePayload {
  name?: string;
  description?: string;
  is_active?: boolean;
}

// =========================================================
// ADD AUDIENCE MEMBER
// =========================================================

export interface AddAudienceMemberPayload {
  customer_id: number;
}

// =========================================================
// BULK MEMBER ADD / CSV IMPORT
// =========================================================

export interface BulkAddAudienceMembersPayload {
  customer_ids: number[];
}

export interface BulkAddAudienceMembersResult {
  audience_id: number;
  requested: number;
  added: number;
  already_members: number;
  member_count: number;
  total_matched: number;
}

export interface BulkAddAudienceMembersResponse {
  success: boolean;
  data: BulkAddAudienceMembersResult;
  message: string;
  meta: Record<string, unknown>;
}

export interface AudienceCsvImportResult {
  audience_id: number;
  total_rows: number;
  imported: number;
  created_customers: number;
  existing_customers: number;
  skipped: number;
  errors: number;
  report: string;
}

export interface AudienceCsvImportResponse {
  success: boolean;
  data: AudienceCsvImportResult;
  message: string;
  meta: Record<string, unknown>;
}
