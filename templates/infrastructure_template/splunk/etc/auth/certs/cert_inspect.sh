#!/usr/local/env bash

# cert_inspect.sh - PEM certificate utility for inspection and validation
#
# Usage:
#   ./cert_inspect.sh --inspect <pem-file>
#   ./cert_inspect.sh --verify <pem-file>
#   ./cert_inspect.sh --validate-cert <server.pem> <ca-chain.pem>

set -euo pipefail

function usage() {
  echo "Usage:"
  echo "  $0 --inspect <pem-file>                      # Inspect subject/issuer of each cert"
  echo "  $0 --verify <pem-file>                       # Verify logical order + strict X.509 validation"
  echo "  $0 --validate-cert <server.pem> <ca.pem>     # Strict validation: clean server cert with CA chain"
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

MODE="$1"
shift

function assert_file_exists() {
  for f in "$@"; do
    [[ -f "$f" ]] || { echo "❌ File not found: $f" >&2; exit 1; }
  done
}

function validate_server_cert() {
  local server_cert="$1"
  local ca_chain="$2"

  echo "🔍 Checking server certificate content..."
  local cert_count
  cert_count=$(grep -c '-----BEGIN CERTIFICATE-----' "$server_cert")

  if (( cert_count > 1 )); then
    echo "⚠️  WARNING: Server certificate '$server_cert' contains multiple certificates ($cert_count)."
    echo "    Splunk requires only the leaf (server) certificate in 'serverCert'."
    echo "    Intermediate and root certificates should be placed in 'caCertFile'."
    echo
  fi

  echo "🔍 Validating server certificate with strict X.509 rules..."
  if openssl verify -verbose -x509_strict -CAfile "$ca_chain" "$server_cert"; then
    echo "✅ Server certificate is valid and trusted by provided CA chain"
  else
    echo "❌ Server certificate validation failed"
    exit 1
  fi
}

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

INPUT_FILE=""
CERT_FILES=()
NUM_CERTS=0

function split_pem() {
  INPUT_FILE="$1"
  csplit -s -z -f "$TMPDIR/cert_" "$INPUT_FILE" '/-----BEGIN CERTIFICATE-----/' '{*}' >/dev/null
  CERT_FILES=("$TMPDIR"/cert_*)
  NUM_CERTS="${#CERT_FILES[@]}"
}

function is_self_signed() {
  local cert_file="$1"
  local subject issuer
  subject=$(openssl x509 -in "$cert_file" -noout -subject 2>/dev/null | sed 's/^subject=//;s/^ *//')
  issuer=$(openssl x509 -in "$cert_file" -noout -issuer 2>/dev/null | sed 's/^issuer=//;s/^ *//')
  [[ "$subject" == "$issuer" ]]
}

function print_cert_info() {
  echo "🔍 Inspecting certificate file: $INPUT_FILE"

  local cert_count
  cert_count=$(grep -c -- '-----BEGIN CERTIFICATE-----' "$INPUT_FILE")
  echo "🔢 Found $cert_count certificate(s) in file"

  if (( cert_count > 1 )); then
    echo "⚠️  WARNING: This file contains multiple certificates."
    echo "    Splunk expects only the server (leaf) certificate in 'serverCert'."
    echo "    Intermediate and root certificates should go in 'caCertFile'."
    echo
  fi

  for cert in "${CERT_FILES[@]}"; do
    echo "=== $(basename "$cert") ==="
    openssl x509 -in "$cert" -noout -subject -issuer || echo "⚠️ Failed to parse $cert"
  done
}

function verify_chain_order_and_strict() {
  local failed=0
  echo "🔍 Checking logical chain order..."

  for i in $(seq 0 $((NUM_CERTS - 2))); do
    current_issuer=$(openssl x509 -in "${CERT_FILES[$i]}" -noout -issuer | sed 's/^issuer=//;s/^ *//')
    next_subject=$(openssl x509 -in "${CERT_FILES[$i+1]}" -noout -subject | sed 's/^subject=//;s/^ *//')
    if [[ "$current_issuer" != "$next_subject" ]]; then
      echo "❌ Mismatch: cert $i issuer != cert $((i+1)) subject"
      echo "    Issuer:  $current_issuer"
      echo "    Subject: $next_subject"
      failed=1
    fi
  done

  last_cert="${CERT_FILES[$((NUM_CERTS - 1))]}"
  if is_self_signed "$last_cert"; then
    echo "✅ Last certificate is self-signed (root CA)"
  else
    echo "❌ The last certificate is not self-signed"
    failed=1
  fi

  echo
  echo "🔐 Running openssl verify -x509_strict..."

  leaf_cert="${CERT_FILES[0]}"
  intermediate_chain="$TMPDIR/intermediates.pem"
  root_ca="$last_cert"

  > "$intermediate_chain"
  for (( i=1; i<NUM_CERTS-1; i++ )); do
    cat "${CERT_FILES[$i]}" >> "$intermediate_chain"
  done
  touch "$intermediate_chain"

  if openssl verify -verbose -x509_strict \
    -CAfile "$root_ca" \
    -untrusted "$intermediate_chain" \
    "$leaf_cert"; then
    echo "✅ Strict OpenSSL verification passed"
  else
    echo "❌ Strict OpenSSL verification failed"
    failed=1
  fi

  if [[ "$failed" -eq 0 ]]; then
    echo "✅ Certificate chain verified successfully"
  else
    echo "❌ Certificate chain verification failed"
    exit 1
  fi
}

# Mode handler
case "$MODE" in
  --inspect)
    assert_file_exists "$1"
    split_pem "$1"
    print_cert_info
    ;;
  --verify)
    assert_file_exists "$1"
    split_pem "$1"
    print_cert_info
    echo
    verify_chain_order_and_strict
    ;;
  --validate-cert)
    if [[ $# -ne 2 ]]; then
      echo "❌ --validate-cert requires exactly 2 arguments" >&2
      usage
    fi
    assert_file_exists "$1" "$2"
    validate_server_cert "$1" "$2"
    ;;
  *)
    echo "❌ Unknown mode: $MODE" >&2
    usage
    ;;
esac