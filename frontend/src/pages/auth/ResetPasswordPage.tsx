import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { isAxiosError } from "axios";
import { resetPassword } from "../../api/auth";
import Alert from "../../components/Alert";

function errorMessage(error: unknown) {
  if (!isAxiosError<Record<string, unknown>>(error)) {
    return "The password could not be reset. Please try again.";
  }
  const data = error.response?.data;
  if (typeof data?.detail === "string") return data.detail;
  for (const key of ["new_password", "confirm_password"]) {
    const value = data?.[key];
    if (Array.isArray(value)) return value.join(" ");
  }
  return "The reset link or password is invalid. Check the form and try again.";
}

export default function ResetPasswordPage() {
  const { uid = "", token = "" } = useParams<{ uid: string; token: string }>();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (password !== confirmPassword) {
      setError("The passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await resetPassword(uid, token, {
        new_password: password,
        confirm_password: confirmPassword,
      });
      setSuccess(data.detail);
      setPassword("");
      setConfirmPassword("");
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
              <h3 className="fw-bold">Choose a new password</h3>
              <p className="text-muted">Reset links expire and can only be used once.</p>
              <Alert message={error} />
              <Alert type="success" message={success} />
              {!success && (
                <form onSubmit={(event) => void handleSubmit(event)}>
                  <div className="mb-3">
                    <label className="form-label" htmlFor="new-password">New password</label>
                    <input
                      id="new-password"
                      type="password"
                      className="form-control"
                      autoComplete="new-password"
                      minLength={8}
                      required
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label" htmlFor="confirm-password">
                      Confirm new password
                    </label>
                    <input
                      id="confirm-password"
                      type="password"
                      className="form-control"
                      autoComplete="new-password"
                      minLength={8}
                      required
                      value={confirmPassword}
                      onChange={(event) => setConfirmPassword(event.target.value)}
                    />
                  </div>
                  <button className="btn btn-primary w-100" type="submit" disabled={loading}>
                    {loading ? "Resetting…" : "Reset password"}
                  </button>
                </form>
              )}
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
