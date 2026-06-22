interface Props { text?: string; }

export default function LoadingSpinner({ text = "Loading…" }: Props) {
  return (
    <div className="d-flex justify-content-center align-items-center p-5">
      <div className="spinner-border text-primary me-3" role="status" aria-hidden="true" />
      <span>{text}</span>
    </div>
  );
}
