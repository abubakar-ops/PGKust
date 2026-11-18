from django.db import migrations, models
import django.db.models.deletion


class AddFieldIfMissing(migrations.AddField):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.model_name)
        column_name = model._meta.get_field(self.name).column
        with schema_editor.connection.cursor() as cursor:
            columns = {
                column.name
                for column in schema_editor.connection.introspection.get_table_description(
                    cursor, model._meta.db_table
                )
            }
        if column_name not in columns:
            super().database_forwards(app_label, schema_editor, from_state, to_state)


def assign_allocation_lecturers(apps, schema_editor):
    CourseMaterial = apps.get_model("courses", "CourseMaterial")
    database = schema_editor.connection.alias
    materials = CourseMaterial.objects.using(database).filter(uploader__isnull=True)
    for material in materials.iterator():
        CourseMaterial.objects.using(database).filter(pk=material.pk).update(
            uploader_id=material.allocation.lecturer_id
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("courses", "0002_academicsession_department_fee"),
    ]

    operations = [
        AddFieldIfMissing(
            model_name="coursematerial",
            name="uploader",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uploaded_materials",
                to="accounts.lecturerprofile",
            ),
        ),
        migrations.RunPython(assign_allocation_lecturers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="coursematerial",
            name="uploader",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uploaded_materials",
                to="accounts.lecturerprofile",
            ),
        ),
    ]
