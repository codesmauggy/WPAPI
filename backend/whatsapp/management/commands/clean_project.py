import os
import shutil
import time
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Delete db.sqlite3, migrations, and cache files'

    def handle(self, *args, **options):
        # Delete database with retry
        db_path = settings.BASE_DIR / 'db.sqlite3'
        if db_path.exists():
            try:
                db_path.unlink()
                self.stdout.write(self.style.SUCCESS('Deleted db.sqlite3'))
            except PermissionError:
                self.stdout.write(self.style.WARNING('Database file is locked. Attempting to force close...'))
                # Try to force close any connections
                import gc
                gc.collect()
                time.sleep(2)
                try:
                    db_path.unlink()
                    self.stdout.write(self.style.SUCCESS('Deleted db.sqlite3 after retry'))
                except PermissionError:
                    self.stdout.write(self.style.ERROR('Could not delete db.sqlite3. Please close any programs using it.'))

        # Delete migration files
        for root, dirs, files in os.walk(settings.BASE_DIR):
            if 'migrations' in dirs:
                migrations_dir = os.path.join(root, 'migrations')
                for file in os.listdir(migrations_dir):
                    if file != '__init__.py' and (file.endswith('.py') or file.endswith('.pyc')):
                        try:
                            os.remove(os.path.join(migrations_dir, file))
                            self.stdout.write(f'Deleted {os.path.join(migrations_dir, file)}')
                        except PermissionError:
                            self.stdout.write(self.style.WARNING(f'Could not delete {file}, skipping...'))

        # Delete cache directories
        for root, dirs, files in os.walk(settings.BASE_DIR):
            if '__pycache__' in dirs:
                cache_dir = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(cache_dir)
                    self.stdout.write(f'Deleted {cache_dir}')
                except PermissionError:
                    self.stdout.write(self.style.WARNING(f'Could not delete {cache_dir}, skipping...'))

        self.stdout.write(self.style.SUCCESS('Project cleaning completed!'))