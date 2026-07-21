#!/bin/bash
# smoke-test.sh — Критические тесты для MIT-лендинга
# Проверяет: HTML-структуру, HTTP-статус, API, форму, мобильную версию, JS-функции
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INDEX_FILE="$SCRIPT_DIR/index.html"
BASE_URL="https://mitoff.ru"
PASS=0
FAIL=0
WARN=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}OK${NC}: $1"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL${NC}: $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "  ${YELLOW}WARN${NC}: $1"; WARN=$((WARN+1)); }

echo "=== MIT Smoke Test ==="
echo ""

# ============================================================
# 1. СТАТИЧЕСКИЕ ПРОВЕРКИ
# ============================================================
echo "--- Статические проверки ---"

# 1a. Файл существует
[ -f "$INDEX_FILE" ] && pass "index.html существует" || fail "index.html не найден"

# 1b. Размер в пределах нормы
BASELINE=340124
CURRENT_SIZE=$(wc -c < "$INDEX_FILE")
MAX_SIZE=$((BASELINE * 110 / 100))
[ "$CURRENT_SIZE" -le "$MAX_SIZE" ] \
  && pass "Размер: $CURRENT_SIZE байт (порог: $MAX_SIZE)" \
  || fail "Размер: $CURRENT_SIZE байт (порог: $MAX_SIZE)"

# 1c. HTML-структура
grep -q '<!DOCTYPE html>' "$INDEX_FILE" && grep -q '</html>' "$INDEX_FILE" \
  && pass "HTML-структура: DOCTYPE, html, head, body" \
  || fail "HTML-структура: не хватает базовых тегов"

# 1d. Мобильная версия
MOBILE_COUNT=$(grep -c 'mobile-version\|mobile-form' "$INDEX_FILE" || true)
[ "$MOBILE_COUNT" -ge 2 ] \
  && pass "Мобильная версия: $MOBILE_COUNT упоминаний" \
  || fail "Мобильная версия: только $MOBILE_COUNT упоминаний"

# 1e. Ключевые секции
SECTIONS=("hero" "telegram" "advantages" "features" "integrations" "skills" "security" "pricing" "faq" "form")
FOUND=0
for s in "${SECTIONS[@]}"; do
    grep -qi "$s" "$INDEX_FILE" 2>/dev/null && FOUND=$((FOUND+1))
done
[ "$FOUND" -ge 7 ] \
  && pass "Ключевые секции: $FOUND/10" \
  || fail "Ключевые секции: $FOUND/10"

# 1f. Баланс div-тегов
OPEN_DIV=$(grep -o '<div' "$INDEX_FILE" | wc -l)
CLOSE_DIV=$(grep -o '</div>' "$INDEX_FILE" | wc -l)
DIFF=$((OPEN_DIV - CLOSE_DIV))
[ "$DIFF" -le 5 ] && [ "$DIFF" -ge -5 ] \
  && pass "Теги div: $OPEN_DIV/$CLOSE_DIV (diff=$DIFF)" \
  || warn "Теги div: $OPEN_DIV/$CLOSE_DIV (diff=$DIFF)"

# 1g. Критические JS-функции присутствуют
for fn in "showSuccessPopup" "setupTelegramInput" "fieldMap"; do
    grep -q "$fn" "$INDEX_FILE" \
      && pass "JS: $fn присутствует" \
      || fail "JS: $fn отсутствует"
done

# 1h. Мета-теги no-cache
grep -q 'no-cache' "$INDEX_FILE" \
  && pass "Мета-теги: no-cache присутствует" \
  || fail "Мета-теги: no-cache отсутствует"

# 1i. Попап (popup) в HTML
grep -q 'mit-popup' "$INDEX_FILE" \
  && pass "Попап: стили и разметка присутствуют" \
  || fail "Попап: отсутствует"

# 1j. Обе формы (десктоп + мобильная)
grep -q 'mobile-form' "$INDEX_FILE" \
  && pass "Формы: мобильная форма присутствует" \
  || fail "Формы: мобильная форма отсутствует"
grep -q 'Application Form' "$INDEX_FILE" \
  && pass "Формы: десктопная форма присутствует" \
  || fail "Формы: десктопная форма отсутствует"

echo ""

# ============================================================
# 2. ПОВЕДЕНЧЕСКИЕ ПРОВЕРКИ (API)
# ============================================================
echo "--- Поведенческие проверки ---"

# 2a. Лендинг открывается
HTTP=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/" 2>/dev/null || echo "000")
[ "$HTTP" = "200" ] \
  && pass "Лендинг: $BASE_URL/ -> $HTTP" \
  || fail "Лендинг: $BASE_URL/ -> $HTTP"

# 2b. API health
API=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/api/health/" 2>/dev/null || echo "000")
[ "$API" = "200" ] \
  && pass "API health: $BASE_URL/api/health/ -> $API" \
  || fail "API health: $BASE_URL/api/health/ -> $API"

# 2c. Форма: валидная заявка → 201
FORM=$(curl -s -w '\n%{http_code}' -X POST "$BASE_URL/api/leads/" \
  -H "Content-Type: application/json" \
  -d '{"last_name":"Смирнов","first_name":"Иван","telegram":"@smoke_test_2024","email":"smoke@test.com","task":"Тестовая задача для smoke-теста"}' 2>/dev/null)
FORM_CODE=$(echo "$FORM" | tail -1)
FORM_BODY=$(echo "$FORM" | head -1)
[ "$FORM_CODE" = "201" ] \
  && pass "Форма (валидная): POST /api/leads/ -> $FORM_CODE" \
  || fail "Форма (валидная): POST /api/leads/ -> $FORM_CODE ($FORM_BODY)"

# 2d. Форма: без @ в telegram → 400
FORM2=$(curl -s -w '\n%{http_code}' -X POST "$BASE_URL/api/leads/" \
  -H "Content-Type: application/json" \
  -d '{"last_name":"Test","first_name":"Test","telegram":"notg","email":"t@t.com","task":"Testing"}' 2>/dev/null)
FORM2_CODE=$(echo "$FORM2" | tail -1)
[ "$FORM2_CODE" = "400" ] \
  && pass "Форма (без @): POST /api/leads/ -> $FORM2_CODE (ожидаем 400)" \
  || fail "Форма (без @): POST /api/leads/ -> $FORM2_CODE (ожидаем 400)"

# 2e. Форма: без email → 400
FORM3=$(curl -s -w '\n%{http_code}' -X POST "$BASE_URL/api/leads/" \
  -H "Content-Type: application/json" \
  -d '{"last_name":"Test","first_name":"Test","telegram":"@testuser","email":"bad","task":"Testing"}' 2>/dev/null)
FORM3_CODE=$(echo "$FORM3" | tail -1)
[ "$FORM3_CODE" = "400" ] \
  && pass "Форма (плохой email): POST /api/leads/ -> $FORM3_CODE (ожидаем 400)" \
  || fail "Форма (плохой email): POST /api/leads/ -> $FORM3_CODE (ожидаем 400)"

# 2f. Форма: пустые обязательные поля → 400
FORM4=$(curl -s -w '\n%{http_code}' -X POST "$BASE_URL/api/leads/" \
  -H "Content-Type: application/json" \
  -d '{"last_name":"","first_name":"","telegram":"","email":"","task":""}' 2>/dev/null)
FORM4_CODE=$(echo "$FORM4" | tail -1)
[ "$FORM4_CODE" = "400" ] \
  && pass "Форма (пустые поля): POST /api/leads/ -> $FORM4_CODE (ожидаем 400)" \
  || fail "Форма (пустые поля): POST /api/leads/ -> $FORM4_CODE (ожидаем 400)"

# 2g. FAQ API
FAQ=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/api/faqs/" 2>/dev/null || echo "000")
[ "$FAQ" = "200" ] \
  && pass "FAQ API: GET /api/faqs/ -> $FAQ" \
  || fail "FAQ API: GET /api/faqs/ -> $FAQ"

# 2h. CORS preflight
CORS=$(curl -s -o /dev/null -w '%{http_code}' -X OPTIONS "$BASE_URL/api/leads/" \
  -H "Origin: https://mitoff.ru" -H "Access-Control-Request-Method: POST" 2>/dev/null || echo "000")
[ "$CORS" = "200" ] \
  && pass "CORS preflight: OPTIONS /api/leads/ -> $CORS" \
  || fail "CORS preflight: OPTIONS /api/leads/ -> $CORS"

# 2i. Nginx no-cache заголовки на HTML
CACHE_HEADER=$(curl -sI "$BASE_URL/" 2>/dev/null | grep -i 'cache-control' || echo "")
echo "$CACHE_HEADER" | grep -qi 'no-cache\|no-store' \
  && pass "Кеширование: Cache-Control запрещает кеш" \
  || warn "Кеширование: Cache-Control не найден"

echo ""

# ============================================================
# 3. ПРОВЕРКА КОНТЕНТА
# ============================================================
echo "--- Проверка контента ---"

# 3a. Поля формы в HTML
grep -qi 'input.*name.*last_name\|input.*name.*first_name\|input.*name.*telegram\|input.*name.*email' "$INDEX_FILE" \
  && pass "Форма: все обязательные поля в HTML" \
  || fail "Форма: не все поля найдены"

# 3b. Текст попапа
grep -q 'Благодарим Вас за заявку' "$INDEX_FILE" \
  && pass "Попап: текст благодарности присутствует" \
  || fail "Попап: текст благодарности отсутствует"

grep -q 'Вы получите на почту сообщение' "$INDEX_FILE" \
  && pass "Попап: текст про почту присутствует" \
  || fail "Попап: текст про почту отсутствует"

# 3c. Кнопка отправки
grep -q 'Запустить МИТ ассистента\|Отправить заявку' "$INDEX_FILE" \
  && pass "Кнопка: текст отправки присутствует" \
  || fail "Кнопка: текст отправки отсутствует"

echo ""
echo "=== Результат ==="
echo -e "  ${GREEN}Пройдено: $PASS${NC}"
echo -e "  ${RED}Провалено: $FAIL${NC}"
echo -e "  ${YELLOW}Предупреждений: $WARN${NC}"
echo ""

[ "$FAIL" -gt 0 ] && echo -e "${RED}SMOKE TEST FAILED${NC}" && exit 1
echo -e "${GREEN}SMOKE TEST PASSED${NC}"
exit 0
