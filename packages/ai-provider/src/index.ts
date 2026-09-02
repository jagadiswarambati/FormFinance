export type ProviderName = 'ollama' | 'gemini' | 'groq';
export interface AIRequest {
  task: string;
  locale: 'en' | 'hi' | 'te';
  schema: object;
  sanitizedContext: string;
}
export interface AIResponse {
  content: object;
  provider: ProviderName;
  model: string;
}
export interface AIProvider {
  readonly name: ProviderName;
  readonly enabled: boolean;
  generate(request: AIRequest): Promise<AIResponse>;
}
export abstract class OllamaProvider implements AIProvider {
  readonly name = 'ollama' as const;
  readonly enabled = true;
  abstract generate(request: AIRequest): Promise<AIResponse>;
}
export abstract class GeminiProvider implements AIProvider {
  readonly name = 'gemini' as const;
  readonly enabled = false;
  abstract generate(request: AIRequest): Promise<AIResponse>;
}
export abstract class GroqProvider implements AIProvider {
  readonly name = 'groq' as const;
  readonly enabled = false;
  abstract generate(request: AIRequest): Promise<AIResponse>;
}
