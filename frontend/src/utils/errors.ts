// Centralised mapping from low-level errors (HttpError, StreamHttpError,
// network failure) to a short user-facing message. Pages should display
// the result of this function; they should never show `error.message`
// directly because backend detail strings, while sanitised, can still
// be implementation-y (e.g. "An internal server error occurred.").

import { HttpError } from "@/services/api";
import { StreamHttpError } from "@/services/streaming";

export const friendlyError = (err: unknown, fallback = "Something went wrong."): string => {
  if (err instanceof StreamHttpError) {
    if (err.status === 401) return "Your session expired. Please sign in again.";
    if (err.status === 403) return "You don't have access to this resource.";
    if (err.status === 404) return "We couldn't find what you were looking for.";
    if (err.status === 413) return "That file is too large.";
    if (err.status === 415) return "That file type isn't supported.";
    if (err.status === 422) return "The request was invalid.";
    if (err.status === 429) return "Too many requests. Please slow down.";
    if (err.status >= 500) return "Our server hit a problem. Please try again.";
    return err.message || fallback;
  }
  if (err instanceof HttpError) {
    if (err.status === 401) return "Your session expired. Please sign in again.";
    if (err.status === 403) return "You don't have access to this resource.";
    if (err.status === 404) return "We couldn't find what you were looking for.";
    if (err.status === 409) return err.message || "That conflicts with existing data.";
    if (err.status === 413) return "That file is too large.";
    if (err.status === 415) return "That file type isn't supported.";
    if (err.status === 422) return "The request was invalid.";
    if (err.status >= 500) return "Our server hit a problem. Please try again.";
    return err.message || fallback;
  }
  if (err instanceof TypeError) {
    // fetch() network failures surface as TypeError.
    return "Can't reach the server. Check your connection.";
  }
  if (err instanceof Error) return err.message;
  return fallback;
};
