# AI Conversation Engine

Milestone 7 implements a conversation-centric API and a provider-neutral backend boundary. Browser code calls only FormWise API routes; it never knows the selected provider or contacts Ollama.

```text
Browser → ConversationService → ContextBuilder → PromptBuilder → AIProvider → ResponseValidator
                                                                ↓
                                                     ConversationRepository
```

## Privacy boundary

`ContextBuilder` loads only `structured_documents/{documentId}` and conversation messages containing safe content. It does not import document storage, OCR, privacy-report, upload, or protected-text services. Redaction markers are removed from the provider context. Sensitive-looking chat input is redacted before persistence and is not submitted to the provider. Provider responses must satisfy a JSON schema, reference only known field IDs, and contain no detected direct identifiers; otherwise a safe fallback is stored and returned.

## API

- `POST /api/v1/conversations` with `{ "documentId": "…" }`
- `GET /api/v1/conversations/{conversationId}`
- `POST /api/v1/conversations/{conversationId}/messages` with `{ "message": "…" }`
- `GET /api/v1/conversations/{conversationId}/messages`
- `DELETE /api/v1/conversations/{conversationId}`

Every route requires Firebase authentication and ownership verification. The document must have completed privacy and understanding before the conversation is created.

## Firestore lifecycle

`conversations/{id}` stores its user, document, state, locale, provider, and timestamps. `messages/{id}` stores only `safeContent`, role, referenced field IDs, provider, usage, latency, and timestamp. There is one active conversation per document.

On a sixth active conversation, the oldest is access-revoked before cascading purge deletes its messages, field answers, rendered outputs, audit records, document metadata, structured document, privacy report, OCR job, and local upload/OCR/protected-text artifacts.

## Ollama configuration

Set `AI_PROVIDER=ollama`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TEMPERATURE`, `OLLAMA_CONTEXT_LENGTH`, `OLLAMA_MAX_TOKENS`, and `OLLAMA_TIMEOUT_SECONDS`. Ollama is the only enabled V1 provider; no cloud fallback exists.
