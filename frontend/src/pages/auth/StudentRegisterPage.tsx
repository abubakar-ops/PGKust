import { useState, type FormEvent, type ChangeEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerStudent } from "../../api/auth";
import Alert from "../../components/Alert";
import type { ProgrammeType } from "../../types";

interface FormState {
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  password: string;
  password_confirm: string;
  matric_number: string;
  programme: ProgrammeType;
  admission_year: number;
}

export default function StudentRegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>({
    email: "", first_name: "", last_name: "", phone_number: "",
    password: "", password_confirm: "", matric_number: "",
    programme: "MSC", admission_year: new Date().getFullYear(),
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const set =
    (k: keyof FormState) =>
    (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    setLoading(true);
    try {
      const payload = { ...form, admission_year: Number(form.admission_year) };
      const { data } = await registerStudent(payload);
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
              <h4 className="fw-bold mb-1">Student Registration</h4>
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
                    <label className="form-label" htmlFor="matric">Matric Number</label>
                    <input id="matric" className="form-control" required value={form.matric_number} onChange={set("matric_number")} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="programme">Programme</label>
                    <select id="programme" className="form-select" value={form.programme} onChange={set("programme")}>
                      <option value="MSC">MSc Computer Science</option>
                      <option value="PHD">PhD Computer Science</option>
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="year">Admission Year</label>
                    <input id="year" type="number" className="form-control" required
                      value={form.admission_year} onChange={set("admission_year")} />
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
