/** Human copy for error codes that arrive in the URL (?error=...) or from the API. */
export const AUTH_ERRORS: Record<string, string> = {
  invalid_credentials: "That email and password don't match.",
  locked: "Too many attempts. Wait a few minutes, or reset your password.",
  throttled: "That's a lot of attempts. Wait a minute and try again.",
  used: "That link was already used. Get a fresh one below.",
  expired: "That link expired. Get a fresh one below.",
  invalid: "That link isn't valid. Get a fresh one below.",
  inactive: "This account is disabled. Contact support if that's a surprise.",
  provider_denied: "Sign-in was cancelled. Try again, or use your email.",
  state_invalid: "We couldn't verify that sign-in. Please try again.",
  state_expired: "Sign-in took too long. Please try again.",
  no_verified_email: "That account has no verified email. Verify one there, or sign in with email.",
  already_linked: "That account is linked to a different Onefold account.",
  provider_error: "We couldn't reach the sign-in provider. Try again.",
  provider_disabled: "That sign-in option isn't available.",
  unavailable: "Onefold's API isn't reachable right now. Try again in a moment.",
  email_taken: "An account with this email already exists.",
  weak_password: "Choose a stronger password.",
};

export function authError(code?: string | null) {
  if (!code) return null;
  return AUTH_ERRORS[code] ?? "Something went wrong signing you in. Please try again.";
}
