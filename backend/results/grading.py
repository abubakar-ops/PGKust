"""
GradingEngine: Pure OOP class implementing the NUC/KUST 5-point grading scale.
No database access - accepts plain numeric inputs, returns computed values.
"""
from decimal import Decimal, ROUND_HALF_UP


class GradingEngine:
    """
    Implements NUC (National Universities Commission) 5-point grading scale
    as mandated for Nigerian universities including KUST.

    Grade Scale (lower bound inclusive, so fractional scores like 69.5 stay in B):
        A  (70-100)    = 5 grade points
        B  (60-<70)    = 4 grade points
        C  (50-<60)    = 3 grade points
        D  (45-<50)    = 2 grade points
        F  (0-<45)     = 0 grade points

    CGPA Classification:
        4.50 - 5.00 = Distinction
        3.50 - 4.49 = Merit
        2.50 - 3.49 = Pass
        < 2.50      = Fail
    """

    # (grade, minimum score, grade point) — checked top-down
    GRADE_SCALE = [
        ('A', 70, 5),
        ('B', 60, 4),
        ('C', 50, 3),
        ('D', 45, 2),
        ('F',  0, 0),
    ]

    CLASSIFICATION_SCALE = [
        ('Distinction', Decimal('4.50'), Decimal('5.00')),
        ('Merit',       Decimal('3.50'), Decimal('4.49')),
        ('Pass',        Decimal('2.50'), Decimal('3.49')),
        ('Fail',        Decimal('0.00'), Decimal('2.49')),
    ]

    MINIMUM_CGPA = Decimal('2.50')

    @classmethod
    def get_grade(cls, score: float) -> str:
        """Return the letter grade for a given numeric score."""
        for grade, low, _ in cls.GRADE_SCALE:
            if score >= low:
                return grade
        return 'F'

    @classmethod
    def get_grade_point(cls, score: float) -> int:
        """Return the grade point (0-5) for a given numeric score."""
        for _, low, gp in cls.GRADE_SCALE:
            if score >= low:
                return gp
        return 0

    @classmethod
    def compute_gpa(cls, courses: list[dict]) -> Decimal:
        """
        Compute GPA for a single semester.

        Args:
            courses: list of dicts, each with:
                     'credit_units' (int) and 'grade_point' (int)

        Returns:
            Decimal GPA rounded to 2 decimal places, or Decimal('0.00') if empty.
        """
        total_quality_points = sum(
            c['credit_units'] * c['grade_point'] for c in courses
        )
        total_credit_units = sum(c['credit_units'] for c in courses)
        if total_credit_units == 0:
            return Decimal('0.00')
        raw = Decimal(str(total_quality_points)) / Decimal(str(total_credit_units))
        return raw.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @classmethod
    def compute_cgpa(cls, all_courses: list[dict]) -> Decimal:
        """
        Compute CGPA across all semesters.

        Args:
            all_courses: list of dicts (same format as compute_gpa, across all semesters)

        Returns:
            Decimal CGPA rounded to 2 decimal places.
        """
        return cls.compute_gpa(all_courses)

    @classmethod
    def classify(cls, cgpa: Decimal) -> str:
        """Return the award classification string for a given CGPA."""
        cgpa = Decimal(str(cgpa))
        for label, low, high in cls.CLASSIFICATION_SCALE:
            if low <= cgpa <= high:
                return label
        return 'Fail'

    @classmethod
    def is_eligible_to_graduate(cls, cgpa: Decimal) -> bool:
        """Return True if CGPA meets the minimum graduation requirement."""
        return Decimal(str(cgpa)) >= cls.MINIMUM_CGPA
