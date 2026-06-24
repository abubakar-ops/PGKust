import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { isAxiosError } from "axios";
import { useAuth } from "../../context/AuthContext";
import Alert from "../../components/Alert";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(email, password);
      if (user.role === "STUDENT") navigate("/student/dashboard");
      else if (user.role === "LECTURER") navigate("/lecturer/dashboard");
      else navigate("/admin/dashboard");
    } catch (err) {
      const detail = isAxiosError<{ detail?: string }>(err) ? err.response?.data?.detail : undefined;
      setError(detail || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-vh-100 d-flex align-items-center bg-light">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-md-5">
            <div className="card shadow-sm border-0">
              <div className="card-body p-4">
                <div className="text-center mb-4">
                  <h3 className="fw-bold text-primary">KUST CS PGMS</h3>
                  <p className="text-muted small">Postgraduate Management System</p>
                </div>
                <Alert message={error} />
                <form onSubmit={(e) => void handleSubmit(e)}>
                  <div className="mb-3">
                    <label className="form-label" htmlFor="email">Email Address</label>
                    <input id="email" type="email" className="form-control" required
                      value={email} onChange={(e) => setEmail(e.target.value)} />
                  </div>
                  <div className="mb-3">
                    <label className="form-label" htmlFor="password">Password</label>
                    <input id="password" type="password" className="form-control" required
                      value={password} onChange={(e) => setPassword(e.target.value)} />
                  </div>
                  <button className="btn btn-primary w-100" type="submit" disabled={loading}>
                    {loading ? "Signing in…" : "Sign In"}
                  </button>
                </form>
                <hr />
                <p className="text-center small mb-0">
                  <Link to="/register/student">Register as Student</Link>
                  {" · "}
                  <Link to="/register/lecturer">Register as Lecturer</Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
