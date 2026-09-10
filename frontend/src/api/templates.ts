import apiClient from "./client";
import type {
  TemplateSyncResponse,
  TemplateSyncResult,
  TemplatesResponse,
  TemplateResponse,
  WhatsAppTemplate,
} from "../types/template";

export interface GetTemplatesParams {
  search?: string;
  category?: string;
  status?: string;
  language?: string;
}

export async function getTemplates(
  params: GetTemplatesParams = {},
): Promise<{
  templates: WhatsAppTemplate[];
  languages: string[];
}> {
  const response = await apiClient.get<TemplatesResponse>("/templates/", {
    params,
  });

  return {
    templates: response.data.data,
    languages: response.data.meta.languages ?? [],
  };
}

export async function getTemplate(
  templateId: number,
): Promise<WhatsAppTemplate> {
  const response = await apiClient.get<TemplateResponse>(
    `/templates/${templateId}/`,
  );

  return response.data.data;
}

export async function syncTemplates(): Promise<TemplateSyncResult> {
  const response = await apiClient.post<TemplateSyncResponse>(
    "/templates/sync/",
  );

  return response.data.data;
}
