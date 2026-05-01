#!/bin/bash
# Deploy script: backup current site, git pull latest, verify
# Run with: sudo bash deploy.sh

set -e

REPO="git@github.com:ivanagxu/sldesign.git"
SITE_DIR="/app/hod"
BACKUP_DIR="/app/hod.bak"
SSH_KEY="/home/aiops/.ssh/id_ed25519_github"
DEPLOY_USER="aiops"

export GIT_SSH_COMMAND="ssh -i $SSH_KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
export HOME="/home/$DEPLOY_USER"

echo "=== SL Design Deploy ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S %Z')"

# Ensure safe.directory for any user running this script
git config --global --add safe.directory "$SITE_DIR" 2>/dev/null || true

# Step 1: Backup current site
if [ -d "$SITE_DIR" ] && [ "$(ls -A $SITE_DIR)" ]; then
    echo "[1/4] Backing up current site..."
    rm -rf "$BACKUP_DIR"
    cp -a "$SITE_DIR" "$BACKUP_DIR"
    echo "  → Backup saved to $BACKUP_DIR"
fi

# Step 2: Clone or pull
if [ -d "$SITE_DIR/.git" ]; then
    echo "[2/4] Pulling latest changes..."
    cd "$SITE_DIR"
    # Discard local changes (permissions/ownership diffs), pull clean
    git checkout -- . 2>/dev/null || true
    git stash --include-untracked 2>/dev/null || true
    git pull origin master
else
    echo "[2/4] Cloning repository..."
    rm -rf "$SITE_DIR"
    git clone "$REPO" "$SITE_DIR"
fi

# Step 3: Set proper ownership so nginx (www-data) can read
echo "[3/4] Setting permissions..."
chown -R www-data:www-data "$SITE_DIR"
chmod -R 755 "$SITE_DIR"

# Verify key files
MISSING=0
for f in index.html news.html news/news-index.json; do
    if [ ! -f "$SITE_DIR/$f" ]; then
        echo "  ✗ Missing: $f"
        MISSING=$((MISSING + 1))
    else
        echo "  ✓ Found: $f"
    fi
done

if [ $MISSING -gt 0 ]; then
    echo "ERROR: $MISSING critical files missing, rolling back..."
    rm -rf "$SITE_DIR"
    mv "$BACKUP_DIR" "$SITE_DIR"
    exit 1
fi

# Step 4: Cleanup
echo "[4/4] Cleanup..."
rm -rf "$BACKUP_DIR"

echo ""
echo "✅ Deploy complete!"
echo "Latest commit: $(cd $SITE_DIR && git log -1 --oneline)"
