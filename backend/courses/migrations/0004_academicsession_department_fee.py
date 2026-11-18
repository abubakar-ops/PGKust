from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models
from django.db.models.functions import Lower


def add_department_fee_column_if_missing(apps, schema_editor):
    connection = schema_editor.connection
    table_name = "courses_academicsession"
    quote_name = connection.ops.quote_name

    with connection.cursor() as cursor:
        columns = connection.introspection.get_table_description(cursor, table_name)
        if any(column.name == "department_fee" for column in columns):
            return

    session_model = apps.get_model("courses", "AcademicSession")
    if session_model.objects.using(connection.alias).exists():
        raise RuntimeError(
            "Cannot add the required department_fee column while academic sessions exist; "
            "configure their actual fees before applying this migration."
        )

    field_type = models.DecimalField(max_digits=10, decimal_places=2).db_type(connection)
    schema_editor.execute(
        f"ALTER TABLE {quote_name(table_name)} "
        f"ADD COLUMN {quote_name('department_fee')} {field_type} NOT NULL"
    )


def ensure_case_insensitive_session_names_are_unique(apps, schema_editor):
    connection = schema_editor.connection
    table_name = "courses_academicsession"
    quote_name = connection.ops.quote_name

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT LOWER({quote_name('name')}), COUNT(*) "
            f"FROM {quote_name(table_name)} "
            f"GROUP BY LOWER({quote_name('name')}) HAVING COUNT(*) > 1"
        )
        if cursor.fetchone():
            raise RuntimeError(
                "Cannot enforce case-insensitive academic session names because duplicates "
                "already exist. Resolve the names without deleting sessions before migrating."
            )


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0003_coursematerial_uploader"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_department_fee_column_if_missing,
                    migrations.RunPython.noop,
                ),
                migrations.RunPython(
                    ensure_case_insensitive_session_names_are_unique,
                    migrations.RunPython.noop,
                ),
                migrations.AddConstraint(
                    model_name="academicsession",
                    constraint=models.UniqueConstraint(
                        Lower("name"),
                        name="unique_academic_session_name_ci",
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="academicsession",
                    name="department_fee",
                    field=models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[MinValueValidator(Decimal("0.01"))],
                    ),
                ),
                migrations.AddConstraint(
                    model_name="academicsession",
                    constraint=models.UniqueConstraint(
                        Lower("name"),
                        name="unique_academic_session_name_ci",
                    ),
                ),
            ],
        ),
    ]
