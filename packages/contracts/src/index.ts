/** Provider-neutral contracts shared by application boundaries. */
export interface ApiError {
  code: string;
  message: string;
  requestId: string;
}
