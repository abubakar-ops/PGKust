"""
GradingEngine: Pure OOP class implementing the NUC/ADUST 5-point grading scale.
No database access - accepts plain numeric inputs, returns computed values.
"""
from decimal import Decimal, ROUND_HALF_UP


class GradingEngine:
    """
    Implements NUC (National Universities Commission) 5-point grading scale
    as mandated for Nigerian universities including ADUST.

    Grade Scale:
        A  (70-100) = 5 grade points
        B  (60-69)  = 4 grade points
        C  (50-59)  = 3 grade points
        D  (45-49)  = 2 grade points
        E  (40-44)  = 1 grade point
        F  (0-39)   = 0 grade points

    CGPA Classification:
        4.50 - 5.00 = First Class
        3.50 - 4.49 = Second Class Upper
        2.40 - 3.49 = Second Class Lower
        1.50 - 2.39 = Third Class
        1.00 - 1.49 = Pass
        < 1.00      = Fail
    """

    GRADE_SCALE = [
        ('A', 70, 100, 5),
        ('B', 60, 69,  4),
        ('C', 50, 59,  3),
        ('D', 45, 49,  2),
        ('E', 40, 44,  1),
        ('F',  0, 39,  0),
    ]

    CLASSIFICATION_SCALE = [
        ('First Class',         Decimal('4.50'), Decimal('5.00')),
        ('Second Class Upper',   Decimal('3.50'), Decimal('4.49')),
        ('Second Class Lower',   Decimal('2.40'), Decimal('3.49')),
        ('Third Class',          Decimal('1.50'), Decimal('2.39')),
        ('Pass',                 Decimal('1.00'), Decimal('1.49')),
        ('Fail',                 Decimal('0.00'), Decimal('0.99')),
    ]

    MINIMUM_CGPA = Decimal('1.00')

    @classmethod
    def get_grade(cls, score: float) -> str:
        """Return the letter grade for a given numeric score."""
        for grade, low, high, _ in cls.GRADE_SCALE:
            if low <= score <= high:
                return grade
        return 'F'

    @classmethod
    def get_grade_point(cls, score: float) -> int:
        """Return the grade point (0-5) for a given numeric score."""
        for _, low, high, gp in cls.GRADE_SCALE:
            if low <= score <= high:
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
