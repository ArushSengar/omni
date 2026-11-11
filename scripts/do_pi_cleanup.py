import exec_pi

cleanup_script = """
set -e
ARCHIVE_DIR="/home/arush/archive_legacy_watchdogs"
mkdir -p "$ARCHIVE_DIR"

echo "=== SAFELY ARCHIVING LEGACY DUPLICATE / OBSOLETE SCRIPTS ==="

# Legacy watchdog scripts in /home/arush
for f in /home/arush/watchdog_*.py /home/arush/watchdog_*.sh /home/arush/run_watchdog.py /home/arush/sys_watchdog.py /home/arush/watchdog.py; do
    if [ -f "$f" ]; then
        echo "Archiving $f"
        mv "$f" "$ARCHIVE_DIR/"
    fi
done

# Legacy check and test scripts in /home/arush
for f in /home/arush/check_*.py /home/arush/health_check*.py /home/arush/test_*.py /home/arush/patch_*.py /home/arush/publish_patch.py /home/arush/save_omniroute_img.py /home/arush/simple_resize.py; do
    if [ -f "$f" ]; then
        echo "Archiving $f"
        mv "$f" "$ARCHIVE_DIR/"
    fi
done

# Legacy docx generation scripts from Sept/Oct
for f in /home/arush/*docx*.py /home/arush/create_doc.py /home/arush/capture_and_build_doc.py /home/arush/make_student_doc.py /home/arush/generate_*.py; do
    if [ -f "$f" ]; then
        echo "Archiving $f"
        mv "$f" "$ARCHIVE_DIR/"
    fi
done

# Workspace legacy test files
if [ -d /home/arush/workspace ]; then
    mkdir -p "$ARCHIVE_DIR/workspace_legacy"
    for f in /home/arush/workspace/check*.py /home/arush/workspace/watchdog*.py /home/arush/workspace/wd_*.py /home/arush/workspace/health_check*.py; do
        if [ -f "$f" ]; then
            echo "Archiving workspace file $f"
            mv "$f" "$ARCHIVE_DIR/workspace_legacy/"
        fi
    done
fi

# Add explanatory README in the archive
cat << 'EOF' > "$ARCHIVE_DIR/ARCHIVE_MANIFEST.md"
# Archived Legacy Scripts
This directory contains archived temporary, debug, and redundant watchdog/check scripts from September-November 2026.
Active production services and cron jobs reside in:
- `/home/arush/.hermes/scripts/watchdog.py` (Active Watchdog Daemon)
- `/home/arush/omni_growth_sentinel.py` (Active Growth Sentinel)
- `/home/arush/omni_daily_growth.py` (Active Daily Growth Engine)
- `/home/arush/growth_reporter_email.py` (Active Email Reporter)
- `/home/arush/maintain.sh` (Active Weekly System Maintenance)
- `/home/arush/omni_hub/` (Active Django Web Dashboard)
EOF

echo ""
echo "Archive completed successfully. Current Python files in /home/arush:"
ls -lh /home/arush/*.py
"""

code, out, err = exec_pi.run_remote(cleanup_script)
print(out)
if err:
    print("STDERR:", err)

