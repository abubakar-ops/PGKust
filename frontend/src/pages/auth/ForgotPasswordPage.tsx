import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { isAxiosError } from "axios";
import { requestPasswordReset } from "../../api/auth";
import Alert from "../../components/Alert";

function errorMessage(error: unknown) {
  if (!isAxiosError<Record<string, unknown>>(error)) {
    return "Unable to submit the request. Please try again.";
  }
  const data = error.response?.data;
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.email)) return data.email.join(" ");
  return "Unable to submit the request. Please check the email address and try again.";
}

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const { data } = await requestPasswordReset(email.trim());
      setSuccess(data.detail);
    } catch (err: unknown) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">
              <h3 className="fw-bold">Forgot password</h3>
              <p className="text-muted">
                Enter the email address associated with your account. If an active
                account matches, a reset link will be sent when email delivery is configured.
              </p>
              <Alert message={error} />
              <Alert type="success" message={success} />
              <form onSubmit={(event) => void handleSubmit(event)}>
                <label className="form-label" htmlFor="reset-email">Email address</label>
                <input
                  id="reset-email"
                  type="email"
                  className="form-control mb-3"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
                <button className="btn btn-primary w-100" type="submit" disabled={loading}>
                  {loading ? "Submitting…" : "Send reset link"}
                </button>
              </form>
              <p className="text-center small mt-3 mb-0">
                <Link to="/login">Back to sign in</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
