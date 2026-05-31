// This will be auto-generated from OpenAPI spec
// For now, we'll define a simple type structure

export interface User {
  id: string;
  email: string;
  phone?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  country?: string | null;
  base_currency: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
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
    transcript?: string | null;
    requestText?: string | null;
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

export interface AiChatMessagePart {
  type: string;
  text?: string | null;
  audio?: AiAudioPayload | null;
}

export interface AiChatMessage {
  id: string;
  role: string;
  content: AiChatMessagePart[];
  metadata?: Record<string, unknown> | null;
  createdAt: string;
}

export interface AiChatConversationSummary {
  id: string;
  title?: string | null;
  lastMessagePreview?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface AiChatConversation {
  id: string;
  userId?: string;
  title?: string | null;
  createdAt: string;
  updatedAt: string;
  messages: AiChatMessage[];
}

export interface AiChatConversationPage {
  items: AiChatConversationSummary[];
  meta: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}

export interface PageMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface Account {
  id: string;
  user_id: string;
  account_type_id: string;
  institution_id: string | null;
  name: string;
  institution_name: string | null;
  currency: string;
  balance: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountList {
  items: Account[];
}

export interface Transaction {
  id: string;
  user_id: string;
  account_id: string;
  category_id: string | null;
  type: string;
  amount: number;
  currency: string;
  transaction_datetime: string;
  description: string | null;
  merchant_id: string | null;
  merchant_name: string | null;
  geo_location: string | null;
  recurring_transaction_id: string | null;
  external_id: string | null;
  transfer_id: string | null;
  transfer_leg: string | null;
  created_at: string;
  tags: Array<{ id: string; user_id: string; name: string }>;
}

export interface TransactionPage {
  items: Transaction[];
  meta: PageMeta;
}

export interface Asset {
  id: string;
  user_id: string;
  asset_type_id: string;
  name: string;
  estimated_value: number;
  currency: string;
  purchase_price: number | null;
  purchase_date: string | null;
  monthly_cost: number | null;
  created_at: string;
  updated_at: string;
}

export interface AssetList {
  items: Asset[];
}

export interface Liability {
  id: string;
  user_id: string;
  liability_type_id: string;
  linked_account_id: string | null;
  collateral_asset_id: string | null;
  name: string;
  creditor_institution_id: string | null;
  creditor_name: string | null;
  original_amount: number | null;
  current_balance: number;
  currency: string;
  interest_rate: number | null;
  interest_type: string | null;
  minimum_payment_amount: number | null;
  regular_payment_amount: number | null;
  payment_due_day: number | null;
  start_date: string | null;
  maturity_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface LiabilityList {
  items: Liability[];
}

export interface FinancialGoal {
  id: string;
  user_id: string;
  name: string;
  target_amount: number;
  current_amount: number;
  deadline: string | null;
  priority: number | null;
  created_at: string;
  updated_at: string;
}

export interface FinancialGoalList {
  items: FinancialGoal[];
}

export interface Transfer {
  id: string;
  user_id: string;
  from_account_id: string;
  to_account_id: string;
  amount: number;
  currency: string;
  transaction_datetime: string;
  description: string | null;
  from_transaction_id: string | null;
  to_transaction_id: string | null;
  from_transaction: Transaction | null;
  to_transaction: Transaction | null;
}

export interface TransferPage {
  items: Transfer[];
  meta: PageMeta;
}

export interface DashboardSummary {
  currency: string;
  total_cash: string;
  total_assets: string;
  total_liabilities: string;
  net_worth: string;
  monthly_income: string;
  monthly_expenses: string;
  savings_rate: number | null;
  upcoming_recurring_transactions: Array<{
    id: string;
    name: string;
    amount: string;
    type: string;
    next_date: string;
  }>;
}

export interface CashFlowPoint {
  period_start: string;
  income: string;
  expenses: string;
  net: string;
}

export interface CashFlowSeries {
  currency: string;
  items: CashFlowPoint[];
}

export interface NetWorthPoint {
  date: string;
  total_cash: string;
  total_assets: string;
  total_liabilities: string;
  net_worth: string;
}

export interface NetWorthSeries {
  currency: string;
  items: NetWorthPoint[];
}
