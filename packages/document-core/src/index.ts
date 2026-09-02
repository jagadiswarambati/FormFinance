export interface DocumentExtractor {
  extract(documentId: string): Promise<void>;
}
export interface PdfRenderer {
  render(documentId: string): Promise<void>;
}
