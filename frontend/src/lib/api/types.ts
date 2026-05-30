// This will be auto-generated from OpenAPI spec
// For now, we'll define a simple type structure

export interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  baseCurrency: string;
  timezone: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  baseCurrency: string;
  timezone: string;
  phone?: string;
  firstName?: string;
  lastName?: string;
  country?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AiChatRequest {
  conversationId?: string | null;
  title?: string | null;
  input: Array<{
    type: 'text' | 'audio';
    text?: string | null;
    audio?: AiAudioPayload | null;
  }>;
  responseModalities?: Array<'text' | 'audio'>;
  audioResponse?: AiAudioResponseOptions;
  context?: AiFinancialContextOptions;
}

export interface AiChatResponse {
  conversationId: string;
  userMessageId: string;
  assistantMessageId: string;
  requestText: string | null;
  output: {
    text: string | null;
    audio: AiAudioPayload | null;
  };
  toolResults?: AiToolResult[];
  usage?: AiUsage;
}

export interface AiAudioPayload {
  contentType: string;
  format?: string | null;
  base64?: string | null;
  url?: string | null;
  durationMs?: number | null;
}

export interface AiAudioResponseOptions {
  voice?: string | null;
  format?: string;
  delivery?: 'inline_base64' | 'temporary_url';
}

export interface AiFinancialContextOptions {
  includeAccounts?: boolean;
  includeTransactions?: boolean;
  includeAssets?: boolean;
  includeLiabilities?: boolean;
  includeGoals?: boolean;
  dateFrom?: string | null;
  dateTo?: string | null;
}

export interface AiToolResult {
  name: string;
  result: Record<string, unknown>;
}

export interface AiUsage {
  inputTokens?: number | null;
  outputTokens?: number | null;
  audioInputSeconds?: number | null;
  audioOutputSeconds?: number | null;
}