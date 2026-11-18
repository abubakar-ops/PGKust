import { useState, useEffect, useCallback } from "react";
import { isAxiosError } from "axios";
import { getFeeStatus, payManual } from "../../api/fees";
import LoadingSpinner from "../../components/LoadingSpinner";
import Alert from "../../components/Alert";
import type { FeePayment } from "../../types";

type FeeStatus = FeePayment | { academic_year: string; status: string };

const STATUS_BADGE: Record<string, string> = {
  APPROVED: "bg-success",
  PENDING: "bg-warning text-dark",
  REJECTED: "bg-danger",
  NOT_PAID: "bg-secondary",
};

export default function StudentFeesPage() {
  const [fee, setFee] = useState<FeeStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [amount, setAmount] = useState("");
  const [receipt, setReceipt] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await getFeeStatus();
      setFee(data);
    } catch {
      setError("Failed to load fee status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!receipt) {
      setError("Please attach your payment receipt.");
      return;
    }
    if (!amount) {
      setError("Please enter the amount paid.");
      return;
    }
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("amount", amount);
      formData.append("receipt", receipt);
      await payManual(formData);
      setSuccess("Payment submitted. It will be reviewed by the admin.");
      setAmount("");
      setReceipt(null);
      await load();
    } catch (err) {
      if (isAxiosError(err)) {
        const data = err.response?.data as { detail?: string } | undefined;
        setError(data?.detail ?? "Failed to submit payment.");
      } else {
        setError("Failed to submit payment.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  const status = fee?.status ?? "NOT_PAID";
  const year = fee?.academic_year ?? "";
  const isPayment = (f: FeeStatus | null): f is FeePayment => !!f && "id" in f;
  const rejectionReason = isPayment(fee) ? fee.rejection_reason : "";

  return (
    <div className="container py-4" style={{ maxWidth: 720 }}>
      <div className="mb-3">
        <h4 className="fw-bold mb-0">Session Registration / Fees</h4>
        <p className="text-muted small mb-0">
          Pay your departmental fee for the current academic session to unlock enrollment-dependent
          features such as course materials.
        </p>
      </div>
      <Alert type="danger" message={error} />
      <Alert type="success" message={success} />

      <div className="card border-0 shadow-sm mb-4">
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
              <div className="text-muted small">Academic Session</div>
              <div className="fw-semibold">{year || "—"}</div>
            </div>
            <span className={`badge ${STATUS_BADGE[status] ?? "bg-secondary"}`}>{status}</span>
          </div>
          {rejectionReason && (
            <div className="alert alert-danger mt-3 mb-0 py-2 small">
              Rejected: {rejectionReason}
            </div>
          )}
        </div>
      </div>

      {status === "APPROVED" ? (
        <div className="alert alert-success">
          Your fee for {year} has been approved. You can now access course materials and other
          session-locked features.
        </div>
      ) : status === "PENDING" ? (
        <div className="alert alert-warning">
          Your payment for {year} is pending admin review. You will be notified once it is approved.
        </div>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="card-body">
            <h6 className="fw-bold mb-3">Submit Manual Payment</h6>
            <form onSubmit={(e) => void handleSubmit(e)}>
              <div className="mb-3">
                <label className="form-label">Amount Paid (₦)</label>
                <input
                  type="number"
                  className="form-control"
                  min="0"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  required
                />
              </div>
              <div className="mb-3">
                <label className="form-label">Payment Receipt</label>
                <input
                  type="file"
                  className="form-control"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => setReceipt(e.target.files?.[0] ?? null)}
                  required
                />
                <div className="form-text">Upload a scanned copy or photo of your bank teller/receipt.</div>
              </div>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Submitting…" : "Submit Payment"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
