#!/bin/bash
set -e

# Disable ANSI colors to prevent colorama/broken pipe issues in Docker
export DJANGO_COLORS=none
export NO_COLOR=1
export FORCE_COLOR=0
export ANSI_COLORS_DISABLED=1
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export DJANGO_NO_COLOR=1
export TERM=dumb
export COLUMNS=80
export LINES=24

# Set signal handling to ignore broken pipe signals
trap '' PIPE

# Function to run Django management commands with error suppression for broken pipe issues
run_django_command() {
    local cmd="$1"
    echo "Running: $cmd"
    
    # Temporarily allow errors and capture the command output
    set +e
    
    # Use timeout to prevent hanging and redirect stderr to filter colorama errors
    timeout 60 bash -c "$cmd" 2>&1 | {
        while IFS= read -r line; do
            # Skip colorama broken pipe error lines and stack traces using case statements for POSIX compatibility
            case "$line" in
                *"BrokenPipeError: [Errno 32] Broken pipe"*) ;;
                *"OSError: [Errno 32] Broken pipe"*) ;;
                "Traceback (most recent call last):"*) ;;
                *"ansitowin32.py"*) ;;
                *"colorama"*) ;;
                *"write_plain_text"*) ;;
                *"self.wrapped.write"*) ;;
                *"write_and_convert"*) ;;
                *"__convertor.write"*) ;;
                *"django/core/management/base.py"*"write"*) ;;
                *"showmigrations.py"*"write"*) ;;
                *"self._out.write"*) ;;
                *"File \"/usr/local/lib/python"*"/site-packages/colorama/"*) ;;
                *"File \"/usr/local/lib/python"*"/site-packages/django/core/management/"*) ;;
                *"File \"/app/manage.py"*) ;;
                *"main()"*) ;;
                *"execute_from_command_line"*) ;;
                *"utility.execute()"*) ;;
                *"self.fetch_command"*) ;;
                *"self.execute("*) ;;
                *"output = self.handle("*) ;;
                *"return self.show_plan("*) ;;
                *"self.stdout.write("*) ;;
                "    "*) ;;  # Filter indented stack trace lines
                *) echo "$line" ;;
            esac
        done
    }
    
    local exit_code=$?
    
    # Re-enable exit on error
    set -e
    
    # Return success if it was just a broken pipe error (exit code 141 from timeout or 32 from broken pipe)
    if [ "${exit_code:-0}" -eq 141 ] || [ "${exit_code:-0}" -eq 32 ]; then
        echo "Command completed (ignoring pipe/timeout issues)"
        return 0
    fi
    
    return ${exit_code:-1}
}

echo "🚀 Starting Kolct Backend..."

# Set default values for missing variables
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@admin.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin12345}
DATABASE_USER=${DATABASE_USER:-postgres}
DATABASE_PASSWORD=${DATABASE_PASSWORD:-postgres}
DATABASE_NAME=${DATABASE_NAME:-postgres}
DATABASE_HOST=${DATABASE_HOST:-kolct_db}
DATABASE_INTERNAL_PORT=${DATABASE_INTERNAL_PORT:-5432}
API_PORT=${API_PORT:-8009}

# Check if using Neon database (cloud) or local database
if [ -n "$NEON_DATABASE_URL" ]; then
	echo "🌐 Using Neon.com serverless database - skipping local database check"
	echo "✅ Neon database configuration detected"
else
	check_postgres() {
		nc -z -w 5 $DATABASE_HOST $DATABASE_INTERNAL_PORT
		return $?
	}

	echo "⏳ Waiting for PostgreSQL at $DATABASE_HOST:$DATABASE_INTERNAL_PORT..."
	until check_postgres; do
		echo "PostgreSQL is unavailable - sleeping"
		sleep 2
	done

	echo "✅ PostgreSQL is accepting connections"
	
	# Additional database readiness check
	echo "🔍 Verifying database readiness..."
	python -c "
import os
import django
from django.conf import settings
from django.db import connection
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        print('✅ Database connection verified')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" || {
		echo "❌ Database verification failed, retrying..."
		sleep 5
		python -c "
import os
import django
from django.conf import settings
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
    print('✅ Database connection verified on retry')
" || {
			echo "❌ Database still not ready after retry"
			exit 1
		}
	}
	
	sleep 2
fi

echo "📦 Collecting static files..."
run_django_command "python manage.py collectstatic --noinput --no-color" || {
	echo "ERROR: Failed to collect static files"
	exit 1
}

echo "🔄 Applying database migrations..."

# Function to cleanup duplicate data before problematic migrations
cleanup_duplicate_data() {
	echo "🧹 Checking and cleaning duplicate data before migrations..."
	
	# Run the cleanup command for duplicate payments
	run_django_command "python manage.py cleanup_duplicate_payments --force" || {
		echo "⚠️ Duplicate payment cleanup failed, but continuing with migrations..."
		echo "ℹ️ This may cause migration 0092 to fail if duplicates exist"
	}
	
	echo "✅ Duplicate data cleanup completed"
}

# Function to check and fix migration dependencies
fix_migration_dependencies() {
	echo "🔍 Checking for migration dependency issues..."
	
	# Check migration status (handle case when django_migrations doesn't exist)
	migration_status=$(run_django_command "python manage.py showmigrations --plan --no-color" 2>&1 || echo "MIGRATION_CHECK_FAILED")
	
	# Check if the migrations table doesn't exist
	if echo "$migration_status" | grep -q "django_migrations\" does not exist"; then
		echo "📝 django_migrations table not found - will be created during migration"
		return 0
	fi
	
	echo "📋 Migration status output:"
	echo "$migration_status"
	
	# Check for any unapplied migrations that might have dependency issues
	unapplied_migrations=$(echo "$migration_status" | grep '\[ \]' | head -5)
	if [ -n "$unapplied_migrations" ]; then
		echo "⚠️ Found unapplied migrations:"
		echo "$unapplied_migrations"
		
		# Try to identify critical user/auth dependencies
		critical_deps=$(echo "$unapplied_migrations" | grep -E '_auth|_user' | head -3)
		if [ -n "$critical_deps" ]; then
			echo "🚨 Critical auth/user migrations found, applying in order..."
			
			# Apply _user migrations first (they typically don't depend on _auth)
			echo "1️⃣ Applying _user migrations first..."
			run_django_command "python manage.py migrate _user --noinput --no-color" || {
				echo "⚠️ _user migrations failed, continuing with fallback..."
			}
			
			# Then apply _auth migrations (which may depend on _user)
			echo "2️⃣ Applying _auth migrations..."
			run_django_command "python manage.py migrate _auth --noinput --no-color" || {
				echo "⚠️ _auth migrations failed, continuing with fallback..."
			}
			
			# Apply other critical core migrations
			for app in contenttypes auth admin sessions; do
				echo "3️⃣ Applying $app migrations..."
				run_django_command "python manage.py migrate $app --noinput --no-color" || {
					echo "⚠️ $app migrations failed, continuing..."
				}
			done
		fi
	else
		echo "✅ No unapplied migrations found"
	fi
}

# Function to handle migration conflicts
resolve_migration_conflicts() {
	echo "🔧 Checking for migration conflicts..."
	
	# Check if there are any merge conflicts in migrations
	run_django_command "python manage.py showmigrations --plan --no-color" | grep -E "CONFLICT|MERGE" && {
		echo "🚨 Migration conflicts detected, attempting automatic resolution..."
		
		# Try to resolve conflicts by running merge migrations
		run_django_command "python manage.py makemigrations --merge --noinput --no-color" || {
			echo "⚠️ Could not auto-resolve migration conflicts"
		}
	} || {
		echo "✅ No migration conflicts detected"
	}
}

# Function to attempt migration recovery
attempt_migration_recovery() {
	echo "🔄 Attempting migration recovery..."
	
	# First, try to resolve any conflicts
	resolve_migration_conflicts
	
	# Check for circular dependencies
	echo "🔍 Checking for circular dependencies..."
	run_django_command "python manage.py migrate --dry-run --noinput --no-color" 2>&1 | grep -i "circular\|dependency" && {
		echo "🚨 Circular dependencies detected, applying targeted fixes..."
		
		# Apply core Django apps first to break circular dependencies
		for app in contenttypes auth sessions admin; do
			echo "🔧 Pre-applying $app to break circular dependencies..."
			run_django_command "python manage.py migrate $app --noinput --no-color" 2>/dev/null || {
				echo "ℹ️ $app migration not needed or already applied"
			}
		done
	}
	
	# Try fake-initial for problematic apps that might have dependency loops
	for app in _auth _user auth contenttypes; do
		echo "🔧 Checking if $app needs fake-initial..."
		run_django_command "python manage.py migrate $app 0001 --fake-initial --noinput --no-color" 2>/dev/null && {
			echo "✅ Applied fake-initial for $app"
		} || {
			echo "ℹ️ No fake-initial needed for $app"
		}
	done
	
	# Try to run migrations again after fake-initial
	echo "🔄 Retrying migrations after recovery attempts..."
	run_django_command "python manage.py migrate --noinput --no-color"
}

# Function to fix corrupted migration state
fix_corrupted_migration_state() {
	echo "🔧 Checking for corrupted migration state..."
	
	# Check if there are missing migration records for existing tables
	python manage.py shell -c "
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
import sys

cursor = connection.cursor()

try:
    # First ensure django_migrations table exists
    cursor.execute(\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'django_migrations'
        );
    \"\"\")
    if not cursor.fetchone()[0]:
        print('📝 django_migrations table does not exist - skipping state check')
        sys.exit(0)
    
    recorder = MigrationRecorder(connection)
    
    # Check for table vs migration record mismatches
    print('Checking for migration state inconsistencies...')
    
    # Check _user app
    cursor.execute(\"SELECT 1 FROM information_schema.tables WHERE table_name='_user_user' LIMIT 1;\")
    user_table_exists = cursor.fetchone() is not None
    
    user_migrations = recorder.migration_qs.filter(app='_user').count()
    print(f'_user_user table exists: {user_table_exists}, migration records: {user_migrations}')
    
    if user_table_exists and user_migrations == 0:
        print('🚨 _user table exists but no migration records found - state corruption detected')
        sys.exit(1)
    
    # Check _auth app  
    cursor.execute(\"SELECT 1 FROM information_schema.tables WHERE table_name='_auth_otp' LIMIT 1;\")
    auth_table_exists = cursor.fetchone() is not None
    
    auth_migrations = recorder.migration_qs.filter(app='_auth').count()
    print(f'_auth_otp table exists: {auth_table_exists}, migration records: {auth_migrations}')
    
    if auth_table_exists and auth_migrations == 0:
        print('🚨 _auth table exists but no migration records found - state corruption detected')
        sys.exit(1)
        
    print('✅ Migration state appears consistent')
    
except Exception as e:
    print(f'Migration state check error: {e}')
    sys.exit(2)
" && echo "✅ Migration state is consistent" || {
		local exit_code=$?
		if [ "${exit_code:-0}" -eq 1 ]; then
			echo "🚨 Corrupted migration state detected, attempting repair..."
			
			# Attempt to repair by faking the initial migrations
			echo "🔧 Faking initial migrations to repair state..."
			run_django_command "python manage.py migrate _user 0001 --fake --noinput --no-color" || echo "Could not fake _user initial"
			run_django_command "python manage.py migrate _auth 0001 --fake --noinput --no-color" || echo "Could not fake _auth initial"
			
			return 1  # Indicate repair was attempted
		else
			echo "⚠️ Could not check migration state"
			return 2  # Indicate check failed
		fi
	}
}

# Function to check for database inconsistencies
check_database_consistency() {
	echo "🔍 Checking database consistency..."
	
	# Check if critical tables exist
	python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
try:
    # First check if django_migrations table exists
    cursor.execute(\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'django_migrations'
        );
    \"\"\")
    migrations_table_exists = cursor.fetchone()[0]
    
    if not migrations_table_exists:
        print('📝 Fresh database detected - django_migrations table does not exist yet')
        print('✅ This is normal for initial setup')
        import sys
        sys.exit(0)
    
    # Check if _user_user table exists
    cursor.execute(\"SELECT 1 FROM information_schema.tables WHERE table_name='_user_user' LIMIT 1;\")
    user_table_exists = cursor.fetchone() is not None
    print(f'_user_user table exists: {user_table_exists}')
    
    # Check if _auth_otp table exists  
    cursor.execute(\"SELECT 1 FROM information_schema.tables WHERE table_name='_auth_otp' LIMIT 1;\")
    auth_table_exists = cursor.fetchone() is not None
    print(f'_auth_otp table exists: {auth_table_exists}')
    
    # Only check migration records if the table exists
    cursor.execute(\"SELECT COUNT(*) FROM django_migrations WHERE app IN ('_user', '_auth');\")
    migration_count = cursor.fetchone()[0]
    print(f'User/Auth migration records: {migration_count}')
    
except Exception as e:
    # Handle the specific case when django_migrations doesn't exist
    if 'relation \"django_migrations\" does not exist' in str(e):
        print('📝 Fresh database - django_migrations table will be created during initial migration')
        print('✅ Proceeding with initial setup')
    else:
        print(f'Database check error: {e}')
" || {
		echo "⚠️ Database consistency check failed but continuing..."
	}
	
	# Only check for corrupted migration state if migrations table exists
	python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute(\"\"\"
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'django_migrations'
    );
\"\"\")
if cursor.fetchone()[0]:
    import sys
    sys.exit(0)
else:
    sys.exit(1)
" && {
		fix_corrupted_migration_state
	} || {
		echo "📝 Skipping migration state check for fresh database"
	}
}

# Function to run command with timeout
run_with_timeout() {
	local timeout_duration=$1
	local command_name=$2
	shift 2
	local command="$@"
	
	echo "⏱️ Running: $command_name (timeout: ${timeout_duration}s)"
	
	# Run command with timeout and capture output
	local output
	output=$(timeout $timeout_duration bash -c "$command" 2>&1)
	local exit_code=$?
	
	# Print the output
	echo "$output"
	
	if [ "${exit_code:-1}" -eq 0 ]; then
		echo "✅ $command_name completed successfully"
		return 0
	elif [ "${exit_code:-1}" -eq 124 ]; then
		echo "⏰ $command_name timed out after ${timeout_duration}s"
		return ${exit_code:-124}
	else
		echo "❌ $command_name failed with exit code: $exit_code"
		return ${exit_code:-1}
	fi
}

# Function to force unlock database if needed
unlock_database() {
	echo "🔓 Checking for database locks..."
	
	# Check for long-running transactions that might block migrations
	python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
try:
    cursor.execute(\"\"\"
        SELECT pid, query, state, query_start 
        FROM pg_stat_activity 
        WHERE state = 'active' 
        AND query_start < NOW() - INTERVAL '5 minutes'
        AND query NOT LIKE '%pg_stat_activity%'
        LIMIT 5
    \"\"\")
    
    long_queries = cursor.fetchall()
    if long_queries:
        print(f'⚠️ Found {len(long_queries)} long-running queries')
        for pid, query, state, start in long_queries:
            print(f'PID {pid}: {query[:100]}... (started: {start})')
    else:
        print('✅ No problematic long-running queries found')
        
except Exception as e:
    print(f'Lock check error: {e}')
" || echo "⚠️ Could not check database locks"
}

# Main migration process with error handling and recovery
perform_migrations() {
	echo "🚀 Starting robust migration process..."
	
	# Check if this is a fresh database that needs initial setup
	IS_FRESH_DB=$(python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
try:
    cursor.execute(\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'django_migrations'
        );
    \"\"\")
    exists = cursor.fetchone()[0]
    print('false' if exists else 'true')
except:
    print('true')
" 2>/dev/null)
	
	if [ "$IS_FRESH_DB" = "true" ]; then
		echo "🆕 Fresh database detected - performing initial setup..."
		echo "📝 Creating django_migrations table and running initial migrations..."
		
		# For fresh databases, run migrations directly without checks
		run_django_command "python manage.py migrate --noinput --no-color" && {
			echo "✅ Initial database setup completed successfully"
			return 0
		} || {
			echo "❌ Initial database setup failed"
			echo "🔍 Attempting fallback initial setup..."
			
			# Try to create core tables first
			run_django_command "python manage.py migrate contenttypes --noinput --no-color" 2>/dev/null || true
			run_django_command "python manage.py migrate auth --noinput --no-color" 2>/dev/null || true
			run_django_command "python manage.py migrate sessions --noinput --no-color" 2>/dev/null || true
			run_django_command "python manage.py migrate admin --noinput --no-color" 2>/dev/null || true
			
			# Then try full migration again
			run_django_command "python manage.py migrate --noinput --no-color" && {
				echo "✅ Database setup completed after fallback"
				return 0
			} || {
				echo "❌ Database setup failed even after fallback"
				return 1
			}
		}
	fi
	
	# Step 1: Check database consistency (for existing databases)
	check_database_consistency
	
	# Step 2: Cleanup duplicate data before migrations
	cleanup_duplicate_data
	
	# Step 3: Check and fix dependencies  
	fix_migration_dependencies
	
	# Step 4: Check for database locks
	unlock_database
	
	# Step 5: Attempt normal migration with timeout
	echo "🔄 Attempting standard migration..."
	
	# Capture both output and exit code using the wrapper function
	set +e
	migration_output=$(run_django_command "python manage.py migrate --noinput --no-color" 2>&1)
	migration_exit_code=$?
	set -e
	
	# Print the output
	echo "$migration_output"
	
	# Check if the error is about unique constraint violation (duplicate payment_ids)
	if echo "$migration_output" | grep -q "could not create unique index.*unique_payment_when_sold" || \
	   echo "$migration_output" | grep -q "IntegrityError.*Key.*payment_id.*duplicated"; then
		echo "🔧 Detected unique constraint violation for payment_ids..."
		echo "📝 This happens when migration 0092 tries to add constraint with existing duplicates"
		
		# Try to clean up duplicates and retry
		echo "🧹 Attempting to clean duplicate payment data and retry..."
		run_django_command "python manage.py cleanup_duplicate_payments --force" && {
			echo "✅ Duplicate cleanup completed, retrying migration..."
			run_django_command "python manage.py migrate --noinput --no-color" && {
				echo "✅ Migration completed after duplicate cleanup"
				return 0
			} || {
				echo "❌ Migration still failed after cleanup"
			}
		} || {
			echo "❌ Could not cleanup duplicates"
		}
		
		# If cleanup doesn't work, try to fake the problematic migration
		echo "🔧 Attempting to fake migration cards.0092..."
		run_django_command "python manage.py migrate cards 0092 --fake --noinput --no-color" && {
			echo "✅ Successfully faked cards.0092 migration"
			echo "🔄 Continuing with remaining migrations..."
			run_django_command "python manage.py migrate --noinput --no-color" && {
				echo "✅ All migrations completed successfully"
				return 0
			} || {
				echo "⚠️ Some migrations still failed"
			}
		} || {
			echo "❌ Could not fake the migration"
		}
		
	# Check if the error is about column already having a default value
	elif echo "$migration_output" | grep -q "column.*already has a default value"; then
		echo "🔧 Detected 'column already has default value' error..."
		echo "📝 This typically happens when a migration tries to alter a column that was already modified"
		
		# Extract the problematic migration
		problematic_migration=$(echo "$migration_output" | grep "Applying" | tail -1 | sed 's/.*Applying //' | sed 's/\.\.\..*//')
		echo "🚨 Problematic migration: $problematic_migration"
		
		if [ -n "$problematic_migration" ]; then
			# Check if it's the issuer.0004 migration we know about
			if echo "$problematic_migration" | grep -q "issuer.0004"; then
				echo "🔧 Known issue with issuer.0004_alter_issuerprofile_id migration"
				echo "📝 This migration tries to alter a column that was already changed to BIGSERIAL in 0003"
				echo "🔄 Attempting to fake this migration..."
				
				run_django_command "python manage.py migrate issuer 0004 --fake --noinput --no-color" && {
					echo "✅ Successfully faked issuer.0004 migration"
					
					# Now try to continue with the rest of migrations
					echo "🔄 Continuing with remaining migrations..."
					run_django_command "python manage.py migrate --noinput --no-color" && {
						echo "✅ All migrations completed successfully"
						return 0
					} || {
						echo "⚠️ Some migrations still failed, but continuing..."
					}
				} || {
					echo "❌ Could not fake the migration"
				}
			else
				# Generic handling for other migrations with the same error
				app_name=$(echo "$problematic_migration" | cut -d'.' -f1)
				migration_name=$(echo "$problematic_migration" | cut -d'.' -f2)
				
				echo "🔧 Attempting to fake migration $app_name.$migration_name..."
				run_django_command "python manage.py migrate $app_name $migration_name --fake --noinput --no-color" && {
					echo "✅ Successfully faked $problematic_migration"
					
					# Continue with remaining migrations
					echo "🔄 Continuing with remaining migrations..."
					run_django_command "python manage.py migrate --noinput --no-color" && {
						echo "✅ All migrations completed successfully"
						return 0
					} || {
						echo "⚠️ Some migrations still failed"
					}
				} || {
					echo "❌ Could not fake the migration"
				}
			fi
		fi
	elif [ $migration_exit_code -ne 0 ]; then
		echo "❌ Standard migration failed with exit code $migration_exit_code, attempting recovery..."
		
		# Step 6: Attempt recovery with timeout
		echo "🔧 Attempting migration recovery..."
		if attempt_migration_recovery; then
			# Try migration again after recovery
			if run_with_timeout 300 "Post-recovery migration" "python manage.py migrate --noinput --no-color"; then
				echo "✅ Migration completed after recovery"
				return 0
			else
				echo "❌ Migration still failed after recovery"
			fi
		else
			echo "❌ Migration recovery process failed"
		fi
		
		# Step 7: Final fallback - continue with warnings
		echo "⚠️ Migration issues detected but continuing startup..."
		echo "📝 Manual intervention may be required"
		
		# Log the current state for debugging
		echo "📊 Final migration state:"
		run_django_command "python manage.py showmigrations --no-color" | grep -E '_auth|_user|admin|auth|contenttypes|issuer' || echo "Could not get migration state"
		
		# Log detailed error information
		echo "🔍 Debug information:"
		echo "Environment: $(echo $DJANGO_SETTINGS_MODULE)"
		echo "Database URL pattern: $(echo $DATABASE_URL | sed 's/:[^@]*@/:***@/g' 2>/dev/null || echo 'Not set')"
		
		return 1
	else
		echo "✅ Standard migration completed successfully"
		return 0
	fi
}

# Execute the migration process
perform_migrations

# Check final migration status
echo "📋 Final migration status check..."
run_django_command "python manage.py showmigrations --plan --no-color | head -20" || echo "Could not retrieve migration status"

echo "✅ Migration process completed"

echo "🏷️ Seeding NFT card categories..."
run_django_command "python manage.py seed_categories" || {
	echo "WARNING: Failed to seed categories, continuing anyway..."
}

echo "💰 Seeding fee settings..."
run_django_command "python manage.py seed_fee_settings" || {
	echo "WARNING: Failed to seed fee settings, continuing anyway..."
}

echo "🎬 Seeding video card animations..."
run_django_command "python manage.py seed_video_animations --force" || {
	echo "WARNING: Failed to seed video animations, continuing anyway..."
}

# Design config seeder removed - no longer needed

echo "👤 Creating/updating admin user..."
# Use a temporary script to avoid shell command complexity with the wrapper function
cat > /tmp/create_admin.py << 'EOF'
import os
import django
from django.conf import settings
from django.db import IntegrityError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.user.models import User

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@admin.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin12345')

admin = User.objects.filter(email=ADMIN_EMAIL).first()
if not admin:
    print(f'Creating new admin user with email: {ADMIN_EMAIL}')
    try:
        admin = User.objects.create_superuser(is_email_verified=True, username='admin', email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        print('✅ Admin user created successfully')
    except IntegrityError as e:
        if 'username' in str(e):
            print('Username admin already exists, trying with email as username...')
            admin = User.objects.create_superuser(is_email_verified=True, username=ADMIN_EMAIL, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
            print('✅ Admin user created successfully with email as username')
        else:
            raise e
else:
    print('Updating existing admin user')
    admin.set_password(ADMIN_PASSWORD)
    admin.is_email_verified = True
    admin.is_superuser = True  # Always ensure superuser status
    admin.is_staff = True      # Always ensure staff status
    admin.is_active = True     # Always ensure active status
    # Only update username if it's different and won't cause conflicts
    if admin.username != 'admin':
        existing_admin_user = User.objects.filter(username='admin').exclude(id=admin.id).first()
        if not existing_admin_user:
            admin.username = 'admin'
        else:
            print('Username admin already taken by another user, keeping current username: ' + admin.username)
    admin.save()
    print('✅ Admin user updated successfully')
    print(f'   Email: {admin.email}')
    print(f'   Is superuser: {admin.is_superuser}')
    print(f'   Is staff: {admin.is_staff}')
    print(f'   Is active: {admin.is_active}')
EOF

run_django_command "python /tmp/create_admin.py"

echo "🤖 Ensuring system account exists..."
# Create a temporary script to ensure system account exists
cat > /tmp/ensure_system_account.py << 'EOF'
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.cards.utils.system_account import ensure_system_account_exists

print("Checking if system account exists...")
if ensure_system_account_exists():
    print("✅ System account is ready")
else:
    print("❌ Failed to ensure system account exists")
    exit(1)
EOF

run_django_command "python /tmp/ensure_system_account.py"

echo "🔥 Warming cache for better performance..."
# Create a temporary script to warm the cache
cat > /tmp/warm_cache.py << 'EOF'
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.cards.cache_managers import CardsCacheManager

print("Warming cache with commonly used data...")
try:
    CardsCacheManager.warm_cache()
    print("✅ Cache warming completed successfully")
except Exception as e:
    print(f"⚠️ Cache warming failed: {e}")
    print("This is not critical - the application will work normally")
EOF

run_django_command "python /tmp/warm_cache.py"

echo "⏰ Syncing Celery Beat scheduled tasks..."
# Create a temporary script to sync Celery Beat tasks
cat > /tmp/sync_celery_beat_tasks.py << 'EOF'
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.core.management import call_command

print("Syncing Celery Beat scheduled tasks...")
try:
    call_command('sync_celery_beat_tasks')
    print("✅ Celery Beat tasks synced successfully")
except Exception as e:
    print(f"⚠️ Failed to sync Celery Beat tasks: {e}")
    print("This is not critical - tasks can be synced manually later")
EOF

run_django_command "python /tmp/sync_celery_beat_tasks.py"

echo "🌐 Starting server on port $API_PORT..."
if [ "$GUNICORN" = "true" ]; then
	echo "Using Gunicorn with ASGI for WebSocket support"
	exec gunicorn --bind 0.0.0.0:$API_PORT --workers 3 -k uvicorn.workers.UvicornWorker config.asgi:application
elif [ "$ENV" = "development" ]; then
	if [ "$USE_WEBSOCKETS" = "true" ]; then
		echo "Using Daphne ASGI server (WebSocket support) for development on port $API_PORT"
		exec daphne -b 0.0.0.0 -p $API_PORT config.asgi:application
	else
		echo "Using Django development server with hot reload on port $API_PORT"
		echo "💡 To enable WebSocket support, set USE_WEBSOCKETS=true in your .env file"
		exec python manage.py runserver 0.0.0.0:$API_PORT
	fi
else
	echo "Using Daphne ASGI server (WebSocket support) on port $API_PORT"
	exec daphne -b 0.0.0.0 -p $API_PORT config.asgi:application
fi
