import apiClient from "./client";

import type { Customer } from "../types/customer";

import type {
  Audience,
  AudienceMember,
  AudiencesResponse,
  AudienceResponse,
  AudienceMembersResponse,
  AudienceMemberResponse,
  AudienceCustomersResponse,
  CreateAudiencePayload,
  UpdateAudiencePayload,
  AddAudienceMemberPayload,
  BulkAddAudienceMembersPayload,
  BulkAddAudienceMembersResponse,
  AudienceCsvImportResponse,
} from "../types/audience";

// =========================================================
// AUDIENCE FILTERS
// =========================================================

export interface AudienceFilters {
  search?: string;
  is_active?: boolean;
}

// =========================================================
// GET AUDIENCES
// =========================================================

export async function getAudiences(
  filters: AudienceFilters = {},
): Promise<Audience[]> {
  const params = new URLSearchParams();

  if (filters.search) {
    params.set("search", filters.search);
  }

  if (filters.is_active !== undefined) {
    params.set(
      "is_active",
      String(filters.is_active),
    );
  }

  const query = params.toString();

  const response =
    await apiClient.get<AudiencesResponse>(
      `/audiences/${
        query ? `?${query}` : ""
      }`,
    );

  return response.data.data;
}

// =========================================================
// CREATE AUDIENCE
// =========================================================

export async function createAudience(
  payload: CreateAudiencePayload,
): Promise<Audience> {
  const response =
    await apiClient.post<AudienceResponse>(
      "/audiences/",
      payload,
    );

  return response.data.data;
}

// =========================================================
// GET AUDIENCE
// =========================================================

export async function getAudience(
  audienceId: number,
): Promise<Audience> {
  const response =
    await apiClient.get<AudienceResponse>(
      `/audiences/${audienceId}/`,
    );

  return response.data.data;
}

// =========================================================
// UPDATE AUDIENCE
// =========================================================

export async function updateAudience(
  audienceId: number,
  payload: UpdateAudiencePayload,
): Promise<Audience> {
  const response =
    await apiClient.patch<AudienceResponse>(
      `/audiences/${audienceId}/`,
      payload,
    );

  return response.data.data;
}

// =========================================================
// DELETE AUDIENCE
// =========================================================

export async function deleteAudience(
  audienceId: number,
): Promise<void> {
  await apiClient.delete(
    `/audiences/${audienceId}/`,
  );
}

// =========================================================
// AUDIENCE MEMBER FILTERS
// =========================================================

export interface AudienceMemberFilters {
  search?: string;
}

// =========================================================
// GET AUDIENCE MEMBERS
// =========================================================

export async function getAudienceMembers(
  audienceId: number,
  filters: AudienceMemberFilters = {},
): Promise<AudienceMember[]> {
  const params = new URLSearchParams();

  if (filters.search) {
    params.set("search", filters.search);
  }

  const query = params.toString();

  const response =
    await apiClient.get<AudienceMembersResponse>(
      `/audiences/${audienceId}/members/${
        query ? `?${query}` : ""
      }`,
    );

  return response.data.data;
}

// =========================================================
// ADD AUDIENCE MEMBER
// =========================================================

export async function addAudienceMember(
  audienceId: number,
  payload: AddAudienceMemberPayload,
): Promise<AudienceMember> {
  const response =
    await apiClient.post<AudienceMemberResponse>(
      `/audiences/${audienceId}/members/`,
      payload,
    );

  return response.data.data;
}

// =========================================================
// REMOVE AUDIENCE MEMBER
// =========================================================

export async function removeAudienceMember(
  audienceId: number,
  customerId: number,
): Promise<void> {
  await apiClient.delete(
    `/audiences/${audienceId}/members/${customerId}/`,
  );
}

// =========================================================
// AVAILABLE CUSTOMERS
// =========================================================

export interface AudienceCustomerFilters {
  search?: string;
  is_active?: boolean;
  marketing_opted_in?: boolean;
}

// =========================================================
// GET AVAILABLE AUDIENCE CUSTOMERS
// =========================================================

export async function getAudienceCustomers(
  audienceId: number,
  filters: AudienceCustomerFilters = {},
): Promise<Customer[]> {
  const params = new URLSearchParams();

  if (filters.search) {
    params.set("search", filters.search);
  }

  if (filters.is_active !== undefined) {
    params.set(
      "is_active",
      String(filters.is_active),
    );
  }

  if (
    filters.marketing_opted_in !== undefined
  ) {
    params.set(
      "marketing_opted_in",
      String(
        filters.marketing_opted_in,
      ),
    );
  }

  const query = params.toString();

  const response =
    await apiClient.get<AudienceCustomersResponse>(
      `/audiences/${audienceId}/customers/${
        query ? `?${query}` : ""
      }`,
    );

  return response.data.data;
}

// =========================================================
// BULK ADD AUDIENCE MEMBERS
// =========================================================

export async function addAudienceMembersBulk(
  audienceId: number,
  payload: BulkAddAudienceMembersPayload,
): Promise<BulkAddAudienceMembersResponse["data"]> {
  const response =
    await apiClient.post<BulkAddAudienceMembersResponse>(
      `/audiences/${audienceId}/members/bulk/`,
      payload,
    );

  return response.data.data;
}

// =========================================================
// CSV IMPORT
// =========================================================

export async function importAudienceCsv(
  audienceId: number,
  file: File,
): Promise<AudienceCsvImportResponse["data"]> {
  const formData = new FormData();
  formData.append("file", file);

  const response =
    await apiClient.post<AudienceCsvImportResponse>(
      `/audiences/${audienceId}/members/import/`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );

  return response.data.data;
}
