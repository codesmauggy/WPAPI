import client from "./client";

import type {
  Campaign,
  CampaignStatistics,
} from "../types/campaign";

/* =========================================================
   TYPES
   ========================================================= */

export interface CampaignPreview {
  campaign_id: number;
  name: string;
  status: string;

  audience?: {
    id: number;
    name: string;
  } | null;

  template?: {
    id: number;
    name: string;
    language?: string;
    status?: string;
  } | null;

  phone_number?: {
    id: number;
    display_phone_number: string;
  } | null;

  statistics?: CampaignStatistics;
}

export interface CampaignStatusResponse {
  id: number;
  name: string;
  status: string;

  statistics: CampaignStatistics;

  progress?: number;
}

export interface CampaignOptions {
  phone_numbers: {
    id: number;
    display_name: string;
    phone_number: string;
    phone_number_id: string;
  }[];

  audiences: {
    id: number;
    name: string;
    description: string;
  }[];

  templates: {
    id: number;
    name: string;
    language: string;
    category: string;
    status: string;
  }[];
}

export interface CreateCampaignPayload {
  name: string;
  phone_number_id: number;
  audience_id: number;
  template_id: number;
}

export interface CreateCampaignResponse {
  campaign_id: number;
  name: string;
  status: string;
}

export interface CampaignRecipientCustomer {
  id: number;
  name: string;
  phone: string;
}

export interface CampaignRecipient {
  id: number;
  phone: string;

  customer: CampaignRecipientCustomer | null;

  status:
    | "PENDING"
    | "QUEUED"
    | "SENDING"
    | "SENT"
    | "DELIVERED"
    | "READ"
    | "FAILED"
    | "CANCELLED";

  whatsapp_message_id: string | null;

  queued_at: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
  failed_at: string | null;

  error_message: string;

  created_at: string;
  updated_at: string;
}

export interface CampaignRecipientsResponse {
  campaign_id: number;
  campaign_name: string;
  total: number;
  recipients: CampaignRecipient[];
}

/* =========================================================
   CAMPAIGN OPTIONS
   ========================================================= */

export async function getCampaignOptions(): Promise<CampaignOptions> {
  const response = await client.get(
    "/campaigns/options/"
  );

  if (!response.data?.success) {
    throw new Error(
      response.data?.error ??
        "Unable to load campaign options."
    );
  }

  return response.data.data;
}


/* =========================================================
   CREATE CAMPAIGN
   ========================================================= */

export async function createCampaign(
  payload: CreateCampaignPayload
): Promise<CreateCampaignResponse> {
  const response = await client.post(
    "/campaigns/create/",
    payload
  );

  if (!response.data?.success) {
    throw new Error(
      response.data?.error ??
        "Unable to create campaign."
    );
  }

  return response.data.data;
}


/* =========================================================
   GET CAMPAIGNS
   ========================================================= */

export async function getCampaigns(): Promise<Campaign[]> {
  const response = await client.get("/campaigns/");

  /*
   * Backend returns:
   *
   * {
   *   success: true,
   *   data: [...]
   * }
   */

  if (!response.data?.success) {
    throw new Error(
      response.data?.error ??
        "Unable to load campaigns."
    );
  }

  return response.data.data ?? [];
}



/* =========================================================
   PREVIEW
   ========================================================= */

export async function getCampaignPreview(
  campaignId: number
) {
  const response = await client.get(
    `/campaigns/${campaignId}/preview/`
  );

  return response.data;
}

/* =========================================================
   GENERATE RECIPIENTS
   ========================================================= */

export async function generateCampaignRecipients(
  campaignId: number
) {
  const response = await client.post(
    `/campaigns/${campaignId}/generate-recipients/`
  );

  if (!response.data?.success) {
    throw new Error(
      response.data?.error ??
        "Unable to generate campaign recipients."
    );
  }

  return response.data;
}

/* =========================================================
   QUEUE CAMPAIGN
   ========================================================= */

export async function queueCampaign(
  campaignId: number
) {
  const response = await client.post(
    `/campaigns/${campaignId}/queue/`
  );

  if (!response.data?.success) {
    throw new Error(
      response.data?.error ??
        "Unable to queue campaign."
    );
  }

  return response.data;
}

/* =========================================================
   GET CAMPAIGN STATUS
   ========================================================= */

export async function getCampaignStatus(
  campaignId: number
) {
  const response = await client.get(
    `/campaigns/${campaignId}/status/`
  );

  return response.data;
}

/* =========================================================
   GET CAMPAIGN RECIPIENTS
   ========================================================= */

export async function getCampaignRecipients(
  campaignId: number
): Promise<CampaignRecipientsResponse> {
  const response = await client.get(
    `/campaigns/${campaignId}/recipients/`
  );

  if (!response.data?.success) {
    throw new Error(
      response.data?.error ??
        "Unable to load campaign recipients."
    );
  }

  return response.data.data;
}

/* =========================================================
   PAUSE
   ========================================================= */

export async function pauseCampaign(
  campaignId: number
) {
  const response = await client.post(
    `/campaigns/${campaignId}/pause/`
  );

  if (!response.data?.success) {
    throw new Error(
      response.data?.error ??
        "Unable to pause campaign."
    );
  }

  return response.data;
}

/* =========================================================
   RESUME
   ========================================================= */

export async function resumeCampaign(
  campaignId: number
) {
  const response = await client.post(
    `/campaigns/${campaignId}/resume/`
  );

  if (!response.data?.success) {
    throw new Error(
      response.data?.error ??
        "Unable to resume campaign."
    );
  }

  return response.data;
}

/* =========================================================
   CANCEL
   ========================================================= */

export async function cancelCampaign(
  campaignId: number
) {
  const response = await client.post(
    `/campaigns/${campaignId}/cancel/`
  );

  if (!response.data?.success) {
    throw new Error(
      response.data?.error ??
        "Unable to cancel campaign."
    );
  }

  return response.data;
}