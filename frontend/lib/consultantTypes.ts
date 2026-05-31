export type ConsultantMessageRole = "user" | "assistant";

export type ConsultantMessageSource = "text" | "voice" | "image";

export type ConsultantMessage = {
  id: string;
  role: ConsultantMessageRole;
  text: string;
  source: ConsultantMessageSource;
  createdAt: string;
  transcript?: string | null;
  audioUrl?: string | null;
  imageUrl?: string | null;
};

export type ConsultantChatState = {
  conversationId: string | null;
  messages: ConsultantMessage[];
};
