interface Props {
  type?: "danger" | "success" | "warning" | "info";
  message: string;
}

export default function Alert({ type = "danger", message }: Props) {
  if (!message) return null;
  return (
    <div className={`alert alert-${type} alert-dismissible fade show`} role="alert">
      {message}
      <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close" />
    </div>
  );
}
