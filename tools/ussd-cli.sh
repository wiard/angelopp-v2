#!/usr/bin/env bash
# ussd-cli.sh
# Terminal-based USSD simulator. Praat met je backend zoals Africa's Talking
# dat doet: POST met sessionId/phoneNumber/serviceCode/text, response moet
# met CON (continue) of END (terminate) beginnen. Input accumuleert met * als
# separator (`text=""` → `text="1"` → `text="1*2"` enz).
#
# Gebruik:
#   ./ussd-cli.sh                                      # default: tester.angelopp.com
#   ./ussd-cli.sh http://localhost:5002/api/ussd       # lokaal tegen Flask
#   PHONE=+254712345678 ./ussd-cli.sh                  # andere phone
#   SERVICE_CODE='*384*66#' ./ussd-cli.sh              # andere shortcode
#   DEBUG=1 ./ussd-cli.sh                              # toon raw text-buffer
#
# Toetsen:
#   <Enter> op een lege regel  → exit
#   q | quit | exit            → exit (zonder END naar server)
#
# Exit codes:
#   0  END ontvangen, sessie netjes afgesloten
#   1  HTTP non-200 of curl-fail
#   2  ctrl+c

set -euo pipefail

URL="${1:-https://tester.angelopp.com/api/ussd}"
PHONE="${PHONE:-+254700000001}"
SERVICE_CODE="${SERVICE_CODE:-*384*466#}"
SESSION_ID="cli-$(date +%s%N | head -c 13)"
TEXT=""
DEBUG="${DEBUG:-0}"
TURN=0

# Colors
BOLD=$'\033[1m'; DIM=$'\033[2m'; GREEN=$'\033[32m'; RED=$'\033[31m'
YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'

trap 'echo; echo "${YELLOW}interrupted${RESET}"; exit 2' INT

printf "%sUSSD CLI%s  →  %s\n" "$BOLD" "$RESET" "$URL"
printf "%ssession=%s  phone=%s  code=%s%s\n\n" \
  "$DIM" "$SESSION_ID" "$PHONE" "$SERVICE_CODE" "$RESET"

while true; do
  TURN=$((TURN + 1))

  if [ "$DEBUG" = "1" ]; then
    printf "%s── turn %d   text=\"%s\"%s\n" "$DIM" "$TURN" "$TEXT" "$RESET"
  fi

  RAW=$(curl -sS -X POST "$URL" \
    -d "sessionId=$SESSION_ID" \
    -d "phoneNumber=$PHONE" \
    -d "serviceCode=$SERVICE_CODE" \
    --data-urlencode "text=$TEXT" \
    -w "\n___STATUS:%{http_code}___" 2>&1) || {
      printf "%s✗ curl failed%s\n" "$RED" "$RESET"
      exit 1
    }

  STATUS=$(printf "%s" "$RAW" | grep -oE '___STATUS:[0-9]+___' | tr -dc '0-9')
  BODY=$(printf "%s" "$RAW" | sed 's/___STATUS:[0-9]*___$//')

  if [ "${STATUS:-000}" != "200" ]; then
    printf "%s✗ HTTP %s%s\n" "$RED" "${STATUS:-???}" "$RESET"
    printf "%s\n" "$BODY"
    exit 1
  fi

  # Eerste 3 chars bepalen flow
  FIRST=$(printf "%s" "$BODY" | head -c 3)
  DISPLAY="${BODY#CON }"
  DISPLAY="${DISPLAY#END }"

  printf "%s┌─────────────────────────────%s\n" "$CYAN" "$RESET"
  printf "%s" "$DISPLAY" | while IFS= read -r line; do
    printf "%s│%s %s\n" "$CYAN" "$RESET" "$line"
  done
  printf "%s└─────────────────────────────%s\n" "$CYAN" "$RESET"

  if [ "$FIRST" = "END" ]; then
    printf "%s✓ END — sessie afgesloten (%d turns)%s\n" "$GREEN" "$TURN" "$RESET"
    exit 0
  fi

  # CON — wacht op input
  printf "→ "
  IFS= read -r INPUT || { echo; exit 0; }

  case "$INPUT" in
    exit|quit|q)
      printf "%sexit (server-side sessie kan nog open staan tot timeout)%s\n" "$YELLOW" "$RESET"
      exit 0
      ;;
    "")
      printf "%sleeg → exit%s\n" "$YELLOW" "$RESET"
      exit 0
      ;;
  esac

  # Accumuleer met * (AT convention)
  if [ -z "$TEXT" ]; then
    TEXT="$INPUT"
  else
    TEXT="${TEXT}*${INPUT}"
  fi
done
