#!/bin/bash
# deploy.sh — Деплой MIT-лендинга с pre/post проверками
# Использование: ./deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INDEX_FILE="$SCRIPT_DIR/index.html"
SMOKE_TEST="$SCRIPT_DIR/smoke-test.sh"
REG_RU_HOST="u3520972@31.31.198.55"
REG_RU_PATH="/var/www/u3520972/data/www/titovtech.ru/assistent/"
VPS_HOST="root@194.67.111.202"
VPS_PATH="/opt/titovtech/static-landing/assistent/"
VPS_PASS="nPKn1BrbLYaUxDFx"
PROD_URL="https://titovtech.ru/assistent/"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "=== MIT Deploy ==="
echo ""

# === Pre-deploy: smoke test ===
echo "--- Pre-deploy: smoke test ---"
if [ -x "$SMOKE_TEST" ]; then
    if "$SMOKE_TEST"; then
        echo -e "${GREEN}Smoke test passed, продолжаем деплой${NC}"
    else
        echo -e "${RED}Smoke test FAILED, деплой остановлен${NC}"
        exit 1
    fi
else
    echo "Smoke test не найден, пропускаем"
fi

echo ""

# === Backup текущей версии ===
echo "--- Backup ---"
BACKUP_NAME="index.html.bak.$(date +%s)"
cp "$INDEX_FILE" "$SCRIPT_DIR/$BACKUP_NAME"
echo "Backup: $BACKUP_NAME"

# === Git commit ===
echo "--- Git ---"
cd "$SCRIPT_DIR"
if git diff --quiet index.html 2>/dev/null; then
    echo "Нет изменений для коммита"
else
    git add index.html
    git commit -m "deploy: $(date -u +%Y-%m-%dT%H:%M:%SZ)" || echo "Коммит пропущен"
fi

echo ""

# === Деплой на REG.RU ===
echo "--- Deploy to REG.RU ---"
scp "$INDEX_FILE" "$REG_RU_HOST:$REG_RU_PATH"
echo -e "${GREEN}REG.RU: done${NC}"

# === Деплой на VPS ===
echo "--- Deploy to VPS ---"
sshpass -p "$VPS_PASS" scp "$INDEX_FILE" "$VPS_HOST:$VPS_PATH"
echo -e "${GREEN}VPS: done${NC}"

echo ""

# === Post-deploy: healthcheck ===
echo "--- Post-deploy: healthcheck ---"
sleep 2

HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "$PROD_URL" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}Healthcheck: $PROD_URL -> $HTTP_CODE${NC}"
else
    echo -e "${RED}Healthcheck FAILED: $PROD_URL -> $HTTP_CODE${NC}"
    echo "Проверь сервер!"
    exit 1
fi

# Проверяем что контент обновился (сравниваем размер)
REMOTE_SIZE=$(curl -s "$PROD_URL" | wc -c)
LOCAL_SIZE=$(wc -c < "$INDEX_FILE")
SIZE_DIFF=$((LOCAL_SIZE - REMOTE_SIZE))
if [ "$SIZE_DIFF" -le 100 ] && [ "$SIZE_DIFF" -ge -100 ]; then
    echo -e "${GREEN}Размер совпадает: локально $LOCAL_SIZE, удалённо $REMOTE_SIZE (diff=$SIZE_DIFF)${NC}"
else
    echo -e "${RED}Размер не совпадает: локально $LOCAL_SIZE, удалённо $REMOTE_SIZE (diff=$SIZE_DIFF)${NC}"
    echo "Возможно кеширование или редирект — проверь вручную"
fi

echo ""
echo -e "${GREEN}=== Deploy complete ===${NC}"
echo "Лендинг: $PROD_URL"
