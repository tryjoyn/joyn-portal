#!/bin/bash
# pre-push-check.sh
# Run before pushing to catch forbidden terms and broken links
# Add to your workflow: ./scripts/pre-push-check.sh && git push

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  JOYN Pre-Push Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Forbidden Terms Check ──────────────────────────────────────────────────────
echo -e "\n${YELLOW}[1/3] Checking for forbidden terms...${NC}"

FORBIDDEN="activate|subscribe|agents(?!\.)|bots|cancel(?!led)|tryjoin"
VIOLATIONS=$(grep -rPn "$FORBIDDEN" --include="*.html" --include="*.js" --include="*.css" . 2>/dev/null | grep -v "node_modules\|pre-push-check\|VISUAL-REGRESSION" || true)

if [ -n "$VIOLATIONS" ]; then
    echo -e "${RED}✗ Forbidden terms found:${NC}"
    echo "$VIOLATIONS"
    echo -e "\n${RED}Fix these before pushing. See docs/VISUAL-REGRESSION-CHECKLIST.md for alternatives.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ No forbidden terms found${NC}"
fi

# ── Broken Anchor Check ────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[2/3] Checking for suspicious href='#'...${NC}"

BROKEN=$(grep -rn 'href="#"' --include="*.html" . 2>/dev/null | grep -v "skip-link\|modal\|onclick\|faq-\|collapse\|dropdown" || true)

if [ -n "$BROKEN" ]; then
    echo -e "${YELLOW}⚠ Potential broken links (may be intentional):${NC}"
    echo "$BROKEN"
    echo -e "\n${YELLOW}Review manually - some may be intentional anchors.${NC}"
else
    echo -e "${GREEN}✓ No suspicious broken links${NC}"
fi

# ── Hardcoded API Keys Check ───────────────────────────────────────────────────
echo -e "\n${YELLOW}[3/3] Checking for hardcoded API keys...${NC}"

# Patterns that look like API keys (32+ hex chars or specific prefixes)
KEYS=$(grep -rPn "sk-[a-zA-Z0-9]{32,}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}" --include="*.html" --include="*.js" . 2>/dev/null | grep -v "\.env\|config\|pre-push" || true)

if [ -n "$KEYS" ]; then
    echo -e "${RED}✗ Possible hardcoded API keys found:${NC}"
    echo "$KEYS"
    echo -e "\n${RED}Move these to environment variables!${NC}"
    exit 1
else
    echo -e "${GREEN}✓ No hardcoded API keys detected${NC}"
fi

# ── Summary ────────────────────────────────────────────────────────────────────
echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Pre-push checks passed! Safe to push.${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
