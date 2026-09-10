import apiClient from "./client";

import type {
  Customer,
  CustomersResponse,
  CustomerResponse,
} from "../types/customer";

// =========================================================
// CUSTOMER FILTERS
// =========================================================

export interface CustomerFilters {
  search?: string;
  status?: string;
  is_active?: boolean;
  marketing_opted_in?: boolean;
  ordering?: string;
}

// =========================================================
// CREATE CUSTOMER
// =========================================================

export interface CreateCustomerPayload {
  name: string;
  phone: string;
  whatsapp_id?: string | null;
  marketing_opted_in?: boolean;
  tags?: string[];
  custom_fields?: Record<
    string,
    unknown
  >;
}

export interface CreateCustomerResponse {
  success: boolean;
  data: Customer;
  message: string;
  meta: Record<string, unknown>;
}

export async function createCustomer(
  payload: CreateCustomerPayload,
): Promise<Customer> {
  const response =
    await apiClient.post<CreateCustomerResponse>(
      "/customers/",
      payload,
    );

  return response.data.data;
}

// =========================================================
// GET CUSTOMERS
// =========================================================

export async function getCustomers(
  filters: CustomerFilters = {},
): Promise<Customer[]> {
  const params =
    new URLSearchParams();

  if (filters.search) {
    params.set(
      "search",
      filters.search,
    );
  }

  if (filters.status) {
    params.set(
      "status",
      filters.status,
    );
  }

  if (
    filters.is_active !==
    undefined
  ) {
    params.set(
      "is_active",
      String(filters.is_active),
    );
  }

  if (
    filters.marketing_opted_in !==
    undefined
  ) {
    params.set(
      "marketing_opted_in",
      String(
        filters.marketing_opted_in,
      ),
    );
  }

  if (filters.ordering) {
    params.set(
      "ordering",
      filters.ordering,
    );
  }

  const query =
    params.toString();

  const response =
    await apiClient.get<CustomersResponse>(
      `/customers/${
        query ? `?${query}` : ""
      }`,
    );

  return response.data.data;
}

// =========================================================
// GET CUSTOMER
// =========================================================

export async function getCustomer(
  customerId: number,
): Promise<Customer> {
  const response =
    await apiClient.get<CustomerResponse>(
      `/customers/${customerId}/`,
    );

  return response.data.data;
}

// =========================================================
// UPDATE CUSTOMER
// =========================================================

export interface UpdateCustomerPayload {
  name?: string;
  phone?: string;
  whatsapp_id?: string | null;
  marketing_opted_in?: boolean;
  tags?: string[];
  custom_fields?: Record<
    string,
    unknown
  >;
  is_active?: boolean;
  status?: string;
}

export interface UpdateCustomerResponse {
  success: boolean;
  data: Customer;
  message: string;
  meta: Record<string, unknown>;
}

export async function updateCustomer(
  customerId: number,
  payload: UpdateCustomerPayload,
): Promise<Customer> {
  const response =
    await apiClient.patch<UpdateCustomerResponse>(
      `/customers/${customerId}/`,
      payload,
    );

  return response.data.data;
}