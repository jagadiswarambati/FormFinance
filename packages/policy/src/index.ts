export type DataClassification = 'SAFE' | 'RESTRICTED' | 'SENSITIVE';
export interface PrivacyPolicy {
  classify(fieldLabel: string): DataClassification;
}
