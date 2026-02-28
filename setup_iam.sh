#!/usr/bin/env bash
#
# setup_iam.sh — Take your already-exported Isengard credentials and
#                configure a named AWS CLI profile from them.
#
# Usage:
#   # Export your Isengard credentials first, then:
#   source ./setup_iam.sh
#   source ./setup_iam.sh --profile my-profile --region us-west-2
#
# Prerequisites:
#   - AWS CLI v2 installed
#   - jq installed (brew install jq)
#   - Isengard credentials already exported (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)

# ──────────────────────────── defaults ────────────────────────────
_PROFILE_NAME="voice-assistant"
_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

# ──────────────────────────── parse args ──────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)  _PROFILE_NAME="$2"; shift 2 ;;
    --region)   _REGION="$2";       shift 2 ;;
    -h|--help)
      echo "Usage: source $0 [--profile NAME] [--region REGION]"
      return 0 2>/dev/null || true ;;
    *) echo "Unknown option: $1"; return 1 2>/dev/null || true ;;
  esac
done

# ──────────────────────── check env vars exist ────────────────────
if [[ -z "${AWS_ACCESS_KEY_ID:-}" || -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
  echo "❌ AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be exported."
  echo "   Export your Isengard credentials first."
  return 1 2>/dev/null || true
fi

# ──────────────────────── verify creds work ───────────────────────
echo "🔑 Verifying current credentials..."
_CALLER=$(aws sts get-caller-identity --output json 2>&1)
if [[ $? -ne 0 ]]; then
  echo "❌ Credentials are invalid or expired."
  echo "   $_CALLER"
  return 1 2>/dev/null || true
fi
echo "   Account:  $(echo "$_CALLER" | jq -r '.Account')"
echo "   Identity: $(echo "$_CALLER" | jq -r '.Arn')"
echo ""

# ──────────────────────── configure CLI profile ───────────────────
echo "� Configuring AWS CLI profile '$_PROFILE_NAME'..."
aws configure set aws_access_key_id     "$AWS_ACCESS_KEY_ID"     --profile "$_PROFILE_NAME"
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY" --profile "$_PROFILE_NAME"
aws configure set region                "$_REGION"               --profile "$_PROFILE_NAME"

if [[ -n "${AWS_SESSION_TOKEN:-}" ]]; then
  aws configure set aws_session_token "$AWS_SESSION_TOKEN" --profile "$_PROFILE_NAME"
fi

# Make sure region env var is set
export AWS_DEFAULT_REGION="$_REGION"

# ──────────────────────── summary ─────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ✅ Done"
echo ""
echo "  CLI Profile:  $_PROFILE_NAME"
echo "  Region:       $_REGION"
echo ""
echo "  Verify with:"
echo "    aws sts get-caller-identity --profile $_PROFILE_NAME"
echo ""
echo "  Start the backend with:"
echo "    ./run_backend.sh --profile $_PROFILE_NAME --region $_REGION"
echo "════════════════════════════════════════════════════════════"

# ──────────────────────── cleanup temp vars ───────────────────────
unset _PROFILE_NAME _REGION _CALLER
