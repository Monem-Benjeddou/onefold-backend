# Generated manually to fix development_stage enum type conflict

from django.db import migrations


def check_and_fix_development_stage_enum(apps, schema_editor):
    """Check if development_stage enum type exists and handle it properly."""
    with schema_editor.connection.cursor() as cursor:
        # Check if the table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'development_stage'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        # Check if the enum type exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'development_stage'
            );
        """)
        enum_exists = cursor.fetchone()[0]
        
        if table_exists and enum_exists:
            # Drop the table first, then the enum type
            cursor.execute("DROP TABLE IF EXISTS development_stage CASCADE;")
            cursor.execute("DROP TYPE IF EXISTS development_stage CASCADE;")
            print("Dropped existing development_stage table and enum type")
        elif enum_exists:
            # Only drop the enum type if table doesn't exist
            cursor.execute("DROP TYPE IF EXISTS development_stage CASCADE;")
            print("Dropped existing development_stage enum type")


def reverse_check_and_fix_development_stage_enum(apps, schema_editor):
    """Reverse operation - no action needed."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            check_and_fix_development_stage_enum,
            reverse_check_and_fix_development_stage_enum,
        ),
    ]
