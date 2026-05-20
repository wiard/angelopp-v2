#!/usr/bin/env bash
# ussd-explore.sh
# Walks all numeric paths through your USSD endpoint up to MAX_DEPTH.
# Skips free-text prompts (via heuristic), skips invalid-input branches,
# saves a tree-rapport naar bestand.
#
# Gebruik:
#   ./ussd-explore.sh                                        # default URL
#   ./ussd-explore.sh http://localhost:5002/api/ussd         # lokaal
#   MAX_DEPTH=3 ./ussd-explore.sh                            # ondieper
#   DIGITS="0 1 2 3 4 5" ./ussd-explore.sh                  # andere digit-set
#   PHONE=+254799999999 ./ussd-explore.sh                    # andere phone
#
# Output: ussd-tree-YYYYMMDD-HHMMSS.txt (en stdout)
#
# Pas FREE_TEXT_PATTERN aan als jouw menu's andere keywords gebruiken
# om om vrije tekst te vragen. Pas INVALID_PATTERN aan voor je eigen
# "ongeldige invoer"-tekst.

set -uo pipefail

URL="${1:-https://tester.angelopp.com/api/ussd}"
PHONE="${PHONE:-+254700000099}"
SERVICE_CODE="${SERVICE_CODE:-*384*466#}"
MAX_DEPTH="${MAX_DEPTH:-4}"
DIGITS="${DIGITS:-1 2 3 4 5 6 7 8 9}"
OUTPUT_FILE="${OUTPUT_FILE:-ussd-tree-$(date +%Y%m%d-%H%M%S).txt}"

FREE_TEXT_PATTERN="naam|beschrijv|vul.*in|voer.*in|enter|adres|kenteken|bericht|hoe heet|wat is.*je|customer message|describe"
INVALID_PATTERN="ongeldig|invalid|tikfout|verkeerd.*invoer|try again|opnieuw|onbekend"

REQUEST_COUNT=0

uniq_sid() {
  echo "explore-$$-$RANDOM-$(date +%s)"
}

ussd_post() {
  local text="$1"
  REQUEST_COUNT=$((REQUEST_COUNT + 1))
  curl -sS -m 5 -X POST "$URL" \
    -d "sessionId=$(uniq_sid)" \
    -d "phoneNumber=$PHONE" \
    -d "serviceCode=$SERVICE_CODE" \
    --data-urlencode "text=$text" 2>/dev/null
}

explore() {
  local text="$1"
  local depth="$2"
  local indent="$3"

  local resp
  resp=$(ussd_post "$text")
  local first="${resp:0:3}"
  local body="${resp#CON }"; body="${body#END }"
  local first_line
  first_line=$(printf "%s" "$body" | head -1)

  printf "%s%s\n" "$indent" "$first_line"

  if [ "$first" = "END" ]; then
    printf "%s  └─ END\n" "$indent"
    return
  fi

  if printf "%s" "$body" | grep -qiE "$FREE_TEXT_PATTERN"; then
    printf "%s  └─ [free text — niet geëxploreerd]\n" "$indent"
    return
  fi

  if [ "$depth" -ge "$MAX_DEPTH" ]; then
    printf "%s  └─ [max depth %s]\n" "$indent" "$MAX_DEPTH"
    return
  fi

  local parent_body="$body"

  for d in $DIGITS; do
    local new_text
    if [ -z "$text" ]; then new_text="$d"; else new_text="${text}*${d}"; fi

    local sub_resp
    sub_resp=$(ussd_post "$new_text")
    local sub_body="${sub_resp#CON }"; sub_body="${sub_body#END }"

    # Skip als response identiek aan parent (optie navigeert niet)
    [ "$sub_body" = "$parent_body" ] && continue

    # Skip "ongeldige invoer"-responses
    if printf "%s" "$sub_body" | grep -qiE "$INVALID_PATTERN"; then
      continue
    fi

    printf "%s  ├─ [%s] →\n" "$indent" "$d"
    explore "$new_text" $((depth + 1)) "${indent}  │   "
  done
}

{
  echo "USSD Menu Explorer"
  echo "URL:          $URL"
  echo "Phone:        $PHONE"
  echo "ServiceCode:  $SERVICE_CODE"
  echo "Max depth:    $MAX_DEPTH"
  echo "Digits:       $DIGITS"
  echo "Started:      $(date)"
  echo "═══════════════════════════════════════════════"
  echo
  explore "" 0 ""
  echo
  echo "═══════════════════════════════════════════════"
  echo "Done. $REQUEST_COUNT requests."
  echo "Finished: $(date)"
} | tee "$OUTPUT_FILE"

echo
echo "Saved to: $OUTPUT_FILE"
