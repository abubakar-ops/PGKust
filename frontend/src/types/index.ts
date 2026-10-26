// ─── Domain types shared across the frontend ─────────────────────────────────

export type UserRole = "STUDENT" | "LECTURER" | "ADMIN";
export type ProgrammeType = "MSC" | "PHD";
export type ProfileStatus = "PENDING" | "ACTIVE" | "SUSPENDED" | "GRADUATED";
export type Semester = "FIRST" | "SECOND";
export type PaymentMethod = "ONLINE" | "MANUAL";
export type PaymentStatus = "PENDING" | "APPROVED" | "REJECTED";
export type ResultBatchStatus = "PENDING" | "APPROVED" | "REJECTED";
export interface ResultBatchCourseProgress {
  allocation: number;
  course_code: string;
  course_title: string;
  lecturer: string;
  lecturer_email: string;
  submitted: boolean;
  result_count: number;
}

export interface ResultBatchProgress {
  expected_course_count: number;
  submitted_course_count: number;
  missing_course_count: number;
  courses: ResultBatchCourseProgress[];
}
export type APRStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "SUPERVISOR_ENDORSED"
  | "COORDINATOR_APPROVED"
  | "REJECTED";

// ─── User / Auth ──────────────────────────────────────────────────────────────

export interface StudentProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number: string;
  matric_number: string;
  programme: ProgrammeType;
  admission_year: number;
  status: ProfileStatus;
  profile_picture: string | null;
  supervisor: number | null;
  supervisor_name: string | null;
  supervisor_email: string | null;
  supervisor_phone_number: string | null;
}

export interface LecturerProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  staff_id: string;
  specialization: string;
  is_supervisor: boolean;
  status: ProfileStatus;
}

export interface AdminProfile {
  id: number;
  email: string;
  full_name: string;
  admin_role: "PG_COORDINATOR" | "HOD";
}

export interface AuthUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  profile: StudentProfile | LecturerProfile | AdminProfile | null;
}

// ─── Courses ──────────────────────────────────────────────────────────────────

export interface AcademicSession {
  id: number;
  name: string;
  is_current: boolean;
  start_date: string;
  end_date: string;
}

export interface Course {
  id: number;
  code: string;
  title: string;
  credit_units: number;
  semester: Semester;
  programme: number;
  programme_name: string;
  is_elective: boolean;
  is_active: boolean;
}

export interface CourseAllocation {
  id: number;
  course: number;
  course_code: string;
  course_title: string;
  credit_units: number;
  lecturer: number;
  lecturer_name: string;
  session: number;
  session_name: string;
  semester: Semester;
  enrolled_count: number;
}

export interface AvailableAllocation {
  id: number;
  course: number;
  course_code: string;
  course_title: string;
  credit_units: number;
  lecturer: number;
  lecturer_name: string;
  session: number;
  session_name: string;
  semester: Semester;
  already_enrolled: boolean;
}

export interface TimetableEntry {
  id: number;
  allocation: number;
  allocation_detail: CourseAllocation;
  day: "MON" | "TUE" | "WED" | "THU" | "FRI";
  start_time: string;
  end_time: string;
  venue: string;
}

export interface Enrollment {
  id: number;
  student: number;
  student_name: string;
  matric_number: string;
  allocation: number;
  course_code: string;
  course_title: string;
  credit_units: number;
  lecturer_name: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  enrolled_at: string;
}

export interface CourseMaterial {
  id: number;
  allocation: number;
  title: string;
  file: string;
  description: string;
  file_available: boolean;
  uploaded_at: string;
}

// ─── Results ─────────────────────────────────────────────────────────────────

export type GradeValue = "A" | "B" | "C" | "D" | "E" | "F";

export interface Result {
  id: number;
  enrollment: number;
  course_code: string;
  course_title: string;
  credit_units: number;
  score: string;
  grade: GradeValue;
  grade_point: string;
  batch: number;
  session_name: string;
  semester: Semester;
}

export interface SemesterResultBatch {
  id: number;
  session: number;
  session_name: string;
  semester: Semester;
  programme_type: ProgrammeType;
  status: ResultBatchStatus;
  coordinator_comment: string;
  approved_at: string | null;
  approved_by: number | null;
  approved_by_name: string | null;
  created_at: string;
  progress: ResultBatchProgress;
}

export interface SemesterGPA {
  id: number;
  session: number;
  session_name: string;
  semester: Semester;
  gpa: string;
  credit_units_earned: number;
}

export interface CumulativeGPA {
  id: number;
  cgpa: string;
  classification: string;
  total_credit_units_earned: number;
  total_quality_points: string;
}

export interface GPAResponse {
  semester_gpas: SemesterGPA[];
  cumulative: CumulativeGPA | null;
}

export interface ExcelUploadRowError {
  row: number;
  registration_no: string;
  detail: string;
}

export interface ExcelUploadResponse {
  uploaded: number;
  errors: ExcelUploadRowError[];
  students_without_scores: string[];
  batch: number;
  batch_status: string;
}

// ─── Fees ─────────────────────────────────────────────────────────────────────

export interface FeePayment {
  id: number;
  student: number;
  student_name: string;
  academic_year: string;
  amount: number;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  transaction_reference: string | null;
  receipt_file: string | null;
  rejection_reason: string;
  approved_at: string | null;
  created_at: string;
}

// ─── Reports / APR ───────────────────────────────────────────────────────────

export interface AnnualProgressReport {
  id: number;
  student: number;
  student_name: string;
  session: number;
  session_name: string;
  year_of_study: number;
  research_progress: string;
  training_activities: string;
  publications: string;
  issues_concerns: string;
  next_year_plan: string;
  status: APRStatus;
  submitted_at: string | null;
  supervisor_comments: string;
  supervisor_endorsed_at: string | null;
  coordinator_comments: string;
  coordinator_approved_at: string | null;
  progression_cleared: boolean;
}

// ─── Notifications ────────────────────────────────────────────────────────────

export interface Notification {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  link: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  count: number;
  results: Notification[];
}
