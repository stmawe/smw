#!/bin/bash

# ============================================================================
# UniMarket Platform - Comprehensive Site Update Script
# ============================================================================
# Purpose: Deploy latest changes, manage static files, restart services
# Protection: Preserves .env and other sensitive files
# Logs: All output logged to dated log files
# ============================================================================

set -e  # Exit on any error

# ============================================================================
# Configuration
# ============================================================================

# Detect environment
if [ "$ENV" != "production" ]; then
    ENV="production"
fi

# Paths - Update these based on your deployment
if [ -z "$REPO_DIR" ]; then
    REPO_DIR="/home/wiptech/domains/smw.cyring.store/public_python/"
fi

VENV_DIR="$REPO_DIR/venv"
STATIC_DIR="$REPO_DIR/static"
MEDIA_DIR="$REPO_DIR/media"
BACKUP_DIR="$REPO_DIR/.backups"
LOG_DIR="/home/wiptech/domains/smw.cyring.store/logs/update"
LOG_FILE="$LOG_DIR/deploy-$(date +'%Y-%m-%d-%H-%M-%S').log"
PID_FILE="/tmp/smw-update.pid"

# Sensitive files to protect
PROTECTED_FILES=(
    ".env"
    ".env.production"
    "db.sqlite3"
    "config/secrets.py"
)

# ============================================================================
# Functions
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE"
}

warning() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" | tee -a "$LOG_FILE"
}

backup_protected_files() {
    log "Backing up protected files..."
    mkdir -p "$BACKUP_DIR"
    
    for file in "${PROTECTED_FILES[@]}"; do
        filepath="$REPO_DIR/$file"
        if [ -f "$filepath" ]; then
            backup_path="$BACKUP_DIR/${file//\//_}.$(date +%s).backup"
            cp "$filepath" "$backup_path"
            log "  Backed up: $file -> $backup_path"
        fi
    done
}

restore_protected_files() {
    log "Restoring protected files..."
    
    for file in "${PROTECTED_FILES[@]}"; do
        filepath="$REPO_DIR/$file"
        # Find the most recent backup
        latest_backup=$(ls -t "$BACKUP_DIR/${file//\//_}".*.backup 2>/dev/null | head -1)
        
        if [ -n "$latest_backup" ]; then
            cp "$latest_backup" "$filepath"
            log "  Restored: $file from $latest_backup"
        else
            warning "  No backup found for: $file"
        fi
    done
}

check_lock() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            error "Update already in progress (PID: $OLD_PID)"
            exit 1
        else
            log "Removing stale lock file"
            rm -f "$PID_FILE"
        fi
    fi
}

acquire_lock() {
    echo $$ > "$PID_FILE"
    log "Lock acquired (PID: $$)"
}

release_lock() {
    rm -f "$PID_FILE"
    log "Lock released"
}

# ============================================================================
# Main Deployment
# ============================================================================

main() {
    log "=========================================="
    log "Starting Site Update (Environment: $ENV)"
    log "=========================================="
    log "Repository: $REPO_DIR"
    log "Virtual Env: $VENV_DIR"
    
    # Check lock
    check_lock
    acquire_lock
    trap release_lock EXIT
    
    # Navigate to repo
    if ! cd "$REPO_DIR"; then
        error "Failed to enter $REPO_DIR"
        exit 1
    fi
    log "Changed to: $(pwd)"
    
    # Activate virtual environment
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        error "Virtual environment not found at $VENV_DIR"
        exit 1
    fi
    source "$VENV_DIR/bin/activate"
    log "Virtual environment activated"
    
    # Backup protected files before pulling
    backup_protected_files
    
    # Stash local changes
    log "Stashing local changes..."
    git stash --include-untracked || true
    
    # Fetch and pull latest changes
    log "Fetching latest changes from origin..."
    git fetch origin main || {
        error "Failed to fetch from origin"
        exit 1
    }
    
    log "Pulling latest changes..."
    git pull origin main || {
        error "Failed to pull from origin"
        exit 1
    }
    
    # Restore protected files
    restore_protected_files
    
    # Reapply local changes
    log "Reapplying local changes..."
    git stash apply || true
    
    # Check for new dependencies
    if git diff HEAD~1 requirements.txt > /dev/null 2>&1; then
        log "Dependencies changed, installing..."
        pip install -r requirements.txt
    fi
    
    # Run Django management commands
    log "Running Django management commands..."
    
    log "  - Checking system..."
    python manage.py check || {
        error "Django system check failed"
        exit 1
    }
    
    log "  - Running migrations..."
    python manage.py migrate_schemas --noinput || {
        error "Migrations failed"
        exit 1
    }
    
    log "  - Collecting static files..."
    python manage.py collectstatic --noinput --clear || {
        error "Collectstatic failed"
        exit 1
    }
    
    # Compress static files if available
    if command -v python manage.py compress &> /dev/null; then
        log "  - Compressing static files..."
        python manage.py compress || warning "Static compression failed (non-critical)"
    fi
    
    # Clear cache
    if command -v python manage.py clear_cache &> /dev/null; then
        log "  - Clearing cache..."
        python manage.py clear_cache || warning "Cache clear failed (non-critical)"
    fi
    
    # Reload or restart services
    log "Reloading web services..."
    
    if command -v devil &> /dev/null; then
        log "  - Restarting via DevilWebPanel..."
        devil www restart smw.cyring.store || {
            warning "DevilWebPanel restart may have failed, trying alternative..."
        }
    fi
    
    # Try to reload gunicorn if running
    if pgrep -f "gunicorn" > /dev/null 2>&1; then
        log "  - Reloading Gunicorn..."
        pkill -HUP -f "gunicorn" || warning "Gunicorn HUP failed"
    fi
    
    # Try to reload uwsgi if running
    if pgrep -f "uwsgi" > /dev/null 2>&1; then
        log "  - Reloading uWSGI..."
        pkill -HUP -f "uwsgi" || warning "uWSGI HUP failed"
    fi
    
    log "=========================================="
    log "Site Update Completed Successfully!"
    log "=========================================="
    log "Next deployment in 2 hours"
    
    return 0
}

# ============================================================================
# Execution
# ============================================================================

# Create log directory
mkdir -p "$LOG_DIR"
exec >> "$LOG_FILE" 2>&1

# Check if running as root for service restarts
if [ "$ENV" = "production" ] && [ $EUID -ne 0 ]; then
    warning "Running as non-root user - service restart may fail"
    warning "Consider running with sudo for production deployments"
fi

# Run main function
main
EXIT_CODE=$?

log "Deployment exit code: $EXIT_CODE"

exit $EXIT_CODE
