import { useState, type FormEvent, type ChangeEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerLecturer } from "../../api/auth";
import Alert from "../../components/Alert";

interface FormState {
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  password: string;
  password_confirm: string;
  staff_id: string;
  specialization: string;
  is_supervisor: boolean;
}

export default function LecturerRegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>({
    email: "", first_name: "", last_name: "", phone_number: "",
    password: "", password_confirm: "", staff_id: "",
    specialization: "", is_supervisor: false,
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const set =
    (k: keyof FormState) =>
    (e: ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    setLoading(true);
    try {
      const { data } = await registerLecturer({ ...form });
      setSuccess(data.detail);
      setTimeout(() => void navigate("/login"), 2500);
    } catch (err: unknown) {
      const resp = (err as { response?: { data?: { errors?: Record<string, string[]> } } }).response;
      const errs = resp?.data?.errors;
      if (errs) {
        setError(Object.entries(errs).map(([k, v]) => `${k}: ${v.join(", ")}`).join(" | "));
      } else {
        setError("Registration failed. Please check your details.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-7">
          <div className="card shadow-sm border-0">
            <div className="card-body p-4">
              <h4 className="fw-bold mb-1">Lecturer Registration</h4>
              <p className="text-muted small mb-3">KUST CS Postgraduate Programme</p>
              <Alert type="danger" message={error} />
              <Alert type="success" message={success} />
              <form onSubmit={(e) => void handleSubmit(e)}>
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="first_name">First Name</label>
                    <input id="first_name" className="form-control" required value={form.first_name} onChange={set("first_name")} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="last_name">Last Name</label>
                    <input id="last_name" className="form-control" required value={form.last_name} onChange={set("last_name")} />
                  </div>
                  <div className="col-12">
                    <label className="form-label" htmlFor="email">Email Address</label>
                    <input id="email" type="email" className="form-control" required value={form.email} onChange={set("email")} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="phone">Phone Number</label>
                    <input id="phone" className="form-control" value={form.phone_number} onChange={set("phone_number")} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="staff_id">Staff ID</label>
                    <input id="staff_id" className="form-control" required value={form.staff_id} onChange={set("staff_id")} />
                  </div>
                  <div className="col-12">
                    <label className="form-label" htmlFor="specialization">Specialization</label>
                    <input id="specialization" className="form-control" value={form.specialization} onChange={set("specialization")} />
                  </div>
                  <div className="col-12">
                    <div className="form-check">
                      <input
                        id="is_supervisor"
                        type="checkbox"
                        className="form-check-input"
                        checked={form.is_supervisor}
                        onChange={(e) => setForm((f) => ({ ...f, is_supervisor: e.target.checked }))}
                      />
                      <label className="form-check-label" htmlFor="is_supervisor">Available as Supervisor</label>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="password">Password</label>
                    <input id="password" type="password" className="form-control" required value={form.password} onChange={set("password")} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="password_confirm">Confirm Password</label>
                    <input id="password_confirm" type="password" className="form-control" required value={form.password_confirm} onChange={set("password_confirm")} />
                  </div>
                  <div className="col-12">
                    <button className="btn btn-primary w-100" type="submit" disabled={loading}>
                      {loading ? "Submitting…" : "Submit Registration"}
                    </button>
                  </div>
                </div>
              </form>
              <p className="text-center small mt-3 mb-0">
                Already registered? <Link to="/login">Sign in</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
