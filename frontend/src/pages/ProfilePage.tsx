import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { isAxiosError } from "axios";
import { changePassword, updateMyProfile } from "../api/auth";
import Alert from "../components/Alert";
import { useAuth } from "../context/AuthContext";

function errorMessage(error: unknown, fallback: string) {
  if (!isAxiosError<Record<string, unknown>>(error)) return fallback;
  const data = error.response?.data;
  if (typeof data?.detail === "string") return data.detail;
  for (const value of Object.values(data ?? {})) {
    if (Array.isArray(value)) return value.join(" ");
    if (typeof value === "string") return value;
  }
  return fallback;
}

export default function ProfilePage() {
  const { user, updateUser, clearSession } = useAuth();
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [phoneNumber, setPhoneNumber] = useState(user?.phone_number ?? "");
  const [picture, setPicture] = useState<File | null>(null);
  const [profileError, setProfileError] = useState("");
  const [profileSuccess, setProfileSuccess] = useState("");
  const [profileLoading, setProfileLoading] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordLoading, setPasswordLoading] = useState(false);

  if (!user) return null;

  async function handleProfileSubmit(event: FormEvent) {
    event.preventDefault();
    setProfileError("");
    setProfileSuccess("");
    setProfileLoading(true);
    const formData = new FormData();
    formData.append("first_name", firstName.trim());
    formData.append("last_name", lastName.trim());
    formData.append("phone_number", phoneNumber.trim());
    if (picture) formData.append("profile_picture", picture);
    try {
      const { data } = await updateMyProfile(formData);
      updateUser(data);
      setPicture(null);
      setProfileSuccess("Your profile has been updated.");
    } catch (err: unknown) {
      setProfileError(errorMessage(err, "Could not update your profile. Please try again."));
    } finally {
      setProfileLoading(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setPasswordError("");
    if (newPassword !== confirmPassword) {
      setPasswordError("The new passwords do not match.");
      return;
    }
    setPasswordLoading(true);
    try {
      const { data } = await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      clearSession();
      navigate("/login", { replace: true, state: { message: data.detail } });
    } catch (err: unknown) {
      setPasswordError(errorMessage(err, "Could not change your password. Please try again."));
    } finally {
      setPasswordLoading(false);
    }
  }

  const profile = user.profile;
  const identifier = profile && "matric_number" in profile
    ? `Matriculation number: ${profile.matric_number}`
    : profile && "staff_id" in profile
      ? `Staff ID: ${profile.staff_id}`
      : null;
  const status = profile && "status" in profile ? profile.status : null;

  return (
    <div className="container py-4" style={{ maxWidth: 800 }}>
      <h2 className="fw-bold mb-4">Profile and security</h2>
      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-white fw-semibold">Account information</div>
        <div className="card-body">
          <div className="row g-3 mb-4">
            <div className="col-md-6">
              <div className="small text-muted">Email (sign-in address)</div>
              <div>{user.email}</div>
            </div>
            <div className="col-md-6">
              <div className="small text-muted">Account type</div>
              <div>{user.role}</div>
            </div>
            {identifier && (
              <div className="col-md-6">
                <div className="small text-muted">Academic identifier</div>
                <div>{identifier}</div>
              </div>
            )}
            {status && (
              <div className="col-md-6">
                <div className="small text-muted">Account status</div>
                <div>{status}</div>
              </div>
            )}
            {user.profile_picture && (
              <div className="col-12">
                <img
                  src={user.profile_picture}
                  alt="Current profile"
                  className="rounded-circle object-fit-cover"
                  width="72"
                  height="72"
                />
              </div>
            )}
          </div>

          <Alert message={profileError} />
          <Alert type="success" message={profileSuccess} />
          <form onSubmit={(event) => void handleProfileSubmit(event)}>
            <div className="row g-3">
              <div className="col-md-6">
                <label className="form-label" htmlFor="profile-first-name">First name</label>
                <input
                  id="profile-first-name"
                  className="form-control"
                  autoComplete="given-name"
                  maxLength={150}
                  required
                  value={firstName}
                  onChange={(event) => setFirstName(event.target.value)}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label" htmlFor="profile-last-name">Last name</label>
                <input
                  id="profile-last-name"
                  className="form-control"
                  autoComplete="family-name"
                  maxLength={150}
                  required
                  value={lastName}
                  onChange={(event) => setLastName(event.target.value)}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label" htmlFor="profile-phone">Phone number</label>
                <input
                  id="profile-phone"
                  className="form-control"
                  autoComplete="tel"
                  maxLength={15}
                  value={phoneNumber}
                  onChange={(event) => setPhoneNumber(event.target.value)}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label" htmlFor="profile-picture">Profile picture</label>
                <input
                  id="profile-picture"
                  type="file"
                  className="form-control"
                  accept="image/*"
                  onChange={(event) => setPicture(event.target.files?.[0] ?? null)}
                />
              </div>
            </div>
            <button className="btn btn-primary mt-3" type="submit" disabled={profileLoading}>
              {profileLoading ? "Saving…" : "Save profile"}
            </button>
          </form>
        </div>
      </div>

      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white fw-semibold">Change password</div>
        <div className="card-body">
          <p className="small text-muted">
            Changing your password signs out this browser and invalidates refresh tokens on other devices.
          </p>
          <Alert message={passwordError} />
          <form onSubmit={(event) => void handlePasswordSubmit(event)}>
            <div className="mb-3">
              <label className="form-label" htmlFor="current-password">Current password</label>
              <input
                id="current-password"
                type="password"
                className="form-control"
                autoComplete="current-password"
                required
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
              />
            </div>
            <div className="row g-3">
              <div className="col-md-6">
                <label className="form-label" htmlFor="profile-new-password">New password</label>
                <input
                  id="profile-new-password"
                  type="password"
                  className="form-control"
                  autoComplete="new-password"
                  minLength={8}
                  required
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label" htmlFor="profile-confirm-password">
                  Confirm new password
                </label>
                <input
                  id="profile-confirm-password"
                  type="password"
                  className="form-control"
                  autoComplete="new-password"
                  minLength={8}
                  required
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                />
              </div>
            </div>
            <button className="btn btn-outline-primary mt-3" type="submit" disabled={passwordLoading}>
              {passwordLoading ? "Changing…" : "Change password"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
