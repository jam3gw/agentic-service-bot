#!/bin/bash
# WebSocket Analysis Script Runner
# This script makes it easier to run the WebSocket analysis script with common options

# Set default values
ENVIRONMENT="dev"
HOURS=24
ANALYSIS="all"
OUTPUT_DIR="./logs"

# Display help message
function show_help {
  echo "WebSocket Analysis Script Runner"
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -e, --environment ENV   Environment to analyze (dev, staging, prod)"
  echo "  -t, --hours HOURS       Hours of logs to analyze"
  echo "  -a, --analysis TYPE     Type of analysis (all, gone, lifecycle, welcome)"
  echo "  -o, --output DIR        Directory to save output logs"
  echo "  -s, --save              Save output to a log file"
  echo "  -h, --help              Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 -e prod -t 48        Analyze production logs for the past 48 hours"
  echo "  $0 -a gone -s           Analyze only GoneException errors and save to log file"
  echo ""
}

# Parse command line arguments
SAVE_OUTPUT=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    -e|--environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    -t|--hours)
      HOURS="$2"
      shift 2
      ;;
    -a|--analysis)
      ANALYSIS="$2"
      shift 2
      ;;
    -o|--output)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -s|--save)
      SAVE_OUTPUT=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Create output directory if it doesn't exist and saving is enabled
if [ "$SAVE_OUTPUT" = true ] && [ ! -d "$OUTPUT_DIR" ]; then
  mkdir -p "$OUTPUT_DIR"
  echo "Created output directory: $OUTPUT_DIR"
fi

# Build the command
CMD="python $(dirname "$0")/analyze_websocket_logs.py --environment $ENVIRONMENT --hours $HOURS --analysis $ANALYSIS"

# Run the command
if [ "$SAVE_OUTPUT" = true ]; then
  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  LOG_FILE="$OUTPUT_DIR/websocket_analysis_${ENVIRONMENT}_${TIMESTAMP}.log"
  echo "Running analysis and saving output to $LOG_FILE"
  $CMD | tee "$LOG_FILE"
  echo "Analysis complete. Log saved to $LOG_FILE"
else
  echo "Running analysis..."
  $CMD
fi 