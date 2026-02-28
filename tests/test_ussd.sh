#!/bin/bash
# Angelopp v2 — Smoke Tests
# Run: bash tests/test_ussd.sh

BASE="http://localhost:5003/ussd"
PHONE="+254700000001"
OK=0
FAIL=0

test_ussd() {
    local desc="$1"
    local text="$2"
    local expect="$3"
    local session="test_$(date +%s%N)"
    
    response=$(curl -s -X POST "$BASE" \
        -d "sessionId=$session&phoneNumber=$PHONE&text=$text")
    
    if echo "$response" | grep -q "$expect"; then
        echo "✅ $desc"
        ((OK++))
    else
        echo "❌ $desc"
        echo "   Expected: $expect"
        echo "   Got: $response"
        ((FAIL++))
    fi
}

echo "=== Angelopp v2 Smoke Tests ==="
echo ""

# Health check
echo "--- Health ---"
health=$(curl -s http://localhost:5003/health)
if [ "$health" = "OK" ]; then
    echo "✅ Health check"
    ((OK++))
else
    echo "❌ Health check"
    ((FAIL++))
fi

echo ""
echo "--- New User Flow ---"
test_ussd "New user sees role selection" "" "Choose your role"
test_ussd "Select Customer role" "1" "Customer Menu"
test_ussd "Customer: new delivery" "1*1" "Where do you want pickup"
test_ussd "Customer: pick landmark" "1*1*1" "Where should we deliver"
test_ussd "Customer: pick destination" "1*1*1*3" "Confirm your delivery"
test_ussd "Customer: confirm order" "1*1*1*3*1" "confirmed"
test_ussd "Customer: cancel order" "1*1*1*3*2" "cancelled"

echo ""
echo "--- Provider Flow ---"
test_ussd "Select Provider role" "2" "Provider Menu"
test_ussd "Provider: set available" "2*1" "Where are you now"
test_ussd "Provider: pick location" "2*1*1" "Confirm"

echo ""
echo "--- Farmer Flow ---"
test_ussd "Select Farmer role" "3" "Farmer Menu"
test_ussd "Farmer: list crop" "3*1" "What are you selling"
test_ussd "Farmer: pick maize" "3*1*1" "Enter quantity"
test_ussd "Farmer: enter quantity" "3*1*1*50kg" "Enter price"
test_ussd "Farmer: enter price" "3*1*1*50kg*500" "Confirm listing"
test_ussd "Farmer: confirm" "3*1*1*50kg*500*1" "Listed"

echo ""
echo "--- Buyer Flow ---"
test_ussd "Select Buyer role" "4" "Buyer Menu"

echo ""
echo "--- Edge Cases ---"
test_ussd "Invalid role" "9" "Invalid"

echo ""
echo "=== Results: $OK passed, $FAIL failed ==="
