export type CustomerStatus = string;

export interface Customer {
  id: number;
  name: string;
  phone: string;
  whatsapp_id: string | null;

  marketing_opted_in: boolean;
  marketing_opted_in_at: string | null;
  marketing_opted_out_at: string | null;

  tags: string[];
  custom_fields: Record<string, unknown>;

  last_message_at: string | null;

  is_active: boolean;
  status: CustomerStatus;

  created_at: string | null;
  updated_at: string | null;
}

export interface CustomersResponse {
  success: boolean;
  data: Customer[];
  message: string;
  meta: {
    total: number;
  };
}

export interface CustomerResponse {
  success: boolean;
  data: Customer;
  message: string;
  meta: Record<string, unknown>;
}