import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_customuser_managers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lecturerprofile',
            name='is_supervisor',
            field=models.BooleanField(
                default=False, help_text='Available to supervise postgraduate students'),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='supervisor',
            field=models.ForeignKey(
                blank=True, help_text='Assigned academic supervisor', null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='supervised_students', to='accounts.lecturerprofile'),
        ),
    ]
