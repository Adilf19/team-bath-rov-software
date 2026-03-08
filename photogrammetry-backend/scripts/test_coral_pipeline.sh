#!/usr/bin/env bash
# Test the photogrammetry pipeline using coral reef images from HuggingFace
# Usage: ./scripts/test_coral_pipeline.sh [num_images]
#
# Downloads images to a temp dir, uploads via API, then runs reconstruction.

set -e

NUM_IMAGES=${1:-15}
BASE_URL="https://huggingface.co/datasets/wildflow/sweet-corals/resolve/main/indonesia_pemuteran_p1_20250213/raw/B1_Left"
API="http://localhost:8100"
START_INDEX=7546
TMP_DIR=$(mktemp -d)

echo "=== Coral Reef Pipeline Test ==="
echo "Images: $NUM_IMAGES"
echo ""

# Check server is running
if ! curl -s --max-time 5 "$API/api/health" > /dev/null 2>&1; then
    echo "ERROR: Server not running at $API"
    echo "Start it with: docker compose -f docker-compose.photogrammetry.yml up -d"
    exit 1
fi

# Create job
JOB=$(curl -s -X POST "$API/api/jobs" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Created job: $JOB"

# Download images to temp dir
echo "Downloading $NUM_IMAGES images..."
END_INDEX=$((START_INDEX + NUM_IMAGES - 1))
for i in $(seq $START_INDEX $END_INDEX); do
    printf "  GPAA%s.JPG... " "$i"
    curl -sL --max-time 30 -o "$TMP_DIR/GPAA${i}.JPG" "${BASE_URL}/GPAA${i}.JPG"
    if [ -s "$TMP_DIR/GPAA${i}.JPG" ]; then
        echo "done ($(du -h "$TMP_DIR/GPAA${i}.JPG" | cut -f1))"
    else
        echo "SKIPPED (download failed)"
        rm -f "$TMP_DIR/GPAA${i}.JPG"
    fi
done
echo "Downloaded $NUM_IMAGES images ($(du -sh "$TMP_DIR" | cut -f1) total)"
echo ""

# Upload via API
echo "Uploading to server..."
UPLOAD_ARGS="-F job_id=$JOB"
for f in "$TMP_DIR"/*.JPG; do
    UPLOAD_ARGS="$UPLOAD_ARGS -F files=@$f"
done
UPLOAD_RESULT=$(eval curl -s -X POST "$API/api/upload" $UPLOAD_ARGS)
echo "$UPLOAD_RESULT" | python3 -m json.tool
echo ""

# Clean up temp files
rm -rf "$TMP_DIR"

# Start pipeline
echo "Starting reconstruction pipeline..."
curl -s -X POST "$API/api/photogrammetry/run" \
    -H "Content-Type: application/json" \
    -d "{\"job_id\": \"$JOB\"}"
echo ""
echo ""

# Poll status
echo "Polling status (Ctrl+C to stop polling, pipeline continues in background)..."
while true; do
    STATUS=$(curl -s --max-time 5 "$API/api/jobs/$JOB" 2>/dev/null)
    STAGE=$(echo "$STATUS" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'{d[\"status\"]:15s} {d[\"progress\"]:3d}%  stage={d.get(\"stage\",\"-\")}')" 2>/dev/null)
    echo "$(date +%H:%M:%S) $STAGE"

    DONE=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    if [ "$DONE" = "COMPLETE" ]; then
        echo ""
        echo "=== SUCCESS ==="
        echo "Download model: curl -o coral_model.glb $API/api/jobs/$JOB/model"
        break
    elif [ "$DONE" = "error" ] || [ "$DONE" = "FAILED" ]; then
        echo ""
        echo "=== FAILED ==="
        echo "$STATUS" | python3 -m json.tool
        break
    fi
    sleep 15
done
