/**
 * Errors thrown by the Namu client. Every error is a `NamuError`; errors the API answered carry its stable `type`
 * (branch on it), the HTTP `status`, a `message` for developers and the `requestId` to send Namu.
 *
 *   NamuError
 *   ├── APIConnectionError        the request did not reach the API, or no answer came back
 *   │   └── APITimeoutError       no answer within the client's timeout
 *   └── APIStatusError            the API answered with an error status
 *       ├── BadRequestError           400
 *       ├── AuthenticationError       401
 *       ├── PermissionDeniedError     403
 *       ├── NotFoundError             404
 *       ├── PayloadTooLargeError      413
 *       ├── UnsupportedAudioError     415
 *       ├── NothingHeardError         422
 *       ├── RateLimitError            429 rate_limited
 *       │   └── QuotaExceededError    429 quota_exceeded (never retried)
 *       └── InternalServerError       5xx
 */

export class NamuError extends Error {
  readonly status?: number;
  readonly type?: string;
  readonly requestId?: string;

  constructor(message: string, opts: { status?: number; type?: string; requestId?: string; cause?: unknown } = {}) {
    const prefix = [opts.status, opts.type].filter((x) => x !== undefined).join(" ");
    super(prefix ? `${prefix}: ${message}${opts.requestId ? ` (request ${opts.requestId})` : ""}` : message,
      opts.cause === undefined ? undefined : { cause: opts.cause });
    this.name = new.target.name;
    this.status = opts.status;
    this.type = opts.type;
    this.requestId = opts.requestId;
  }
}

export class APIConnectionError extends NamuError {}
export class APITimeoutError extends APIConnectionError {}

export class APIStatusError extends NamuError {
  declare readonly status: number;
  declare readonly type: string;
}
export class BadRequestError extends APIStatusError {}
export class AuthenticationError extends APIStatusError {}
export class PermissionDeniedError extends APIStatusError {}
export class NotFoundError extends APIStatusError {}
export class PayloadTooLargeError extends APIStatusError {}
export class UnsupportedAudioError extends APIStatusError {}
export class NothingHeardError extends APIStatusError {}
export class RateLimitError extends APIStatusError {}
export class QuotaExceededError extends RateLimitError {}
export class InternalServerError extends APIStatusError {}

const BY_STATUS: Record<number, typeof APIStatusError> = {
  400: BadRequestError, 401: AuthenticationError, 403: PermissionDeniedError, 404: NotFoundError,
  413: PayloadTooLargeError, 415: UnsupportedAudioError, 422: NothingHeardError, 429: RateLimitError,
};

/** The most specific error class for an API answer. */
export function errorFor(status: number, type: string, message: string, requestId?: string): APIStatusError {
  const Cls = status === 429 && type === "quota_exceeded" ? QuotaExceededError
    : status >= 500 ? InternalServerError
    : BY_STATUS[status] ?? APIStatusError;
  return new Cls(message, { status, type, requestId });
}
