# =====================================================
# FIX + DEPLOY 1-SHOT — paste nguyên block này vào VPS
# Chạy trên VPS root@161.248.4.99
# =====================================================
cd /opt/appdk
echo "=== [1/5] Check repo ==="
ls apps/web/package.json 2>/dev/null && echo "OK: code có" || echo "FAIL: clone lại"
echo ""
echo "=== [2/5] Nếu fail → clone sạch ==="
if [ ! -f apps/web/package.json ]; then
    find . -mindepth 1 -maxdepth 1 ! -name '.env.production' ! -name 'env.sh' -exec rm -rf {} +
    GIT_TERMINAL_PROMPT=0 git clone https://github.com/thuanndbxvp/duongk_app.git .
fi
ls apps/web/package.json
echo ""
echo "=== [3/5] Restore .env.production ==="
mv /root/.env.production /opt/appdk/.env.production 2>/dev/null
test -f .env.production || echo "WARNING: thiếu .env.production → nano điền sau"
chmod 600 .env.production 2>/dev/null
echo ""
echo "=== [4/5] git pull ==="
GIT_TERMINAL_PROMPT=0 git pull origin main
echo ""
echo "=== [5/5] Deploy ==="
chmod +x deploy.sh
./deploy.sh --logs