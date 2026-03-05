#!/usr/bin/env bash
# Test the photogrammetry pipeline using coral reef images from HuggingFace
# Usage: ./scripts/test_coral_pipeline.sh [num_images]
#
# Downloads images directly into the Docker container (no local storage needed)
# then runs the full reconstruction pipeline.

set -e

NUM_IMAGES=${1:-15}
BASE_URL="https://huggingface.co/datasets/wildflow/sweet-corals/resolve/main/indonesia_pemuteran_p1_20250213/raw/B1_Left"
API="http://localhost:8100"
START_INDEX=7546

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

# Download images directly into the container
echo "Downloading $NUM_IMAGES images into container..."
END_INDEX=$((START_INDEX + NUM_IMAGES - 1))
docker exec team-bath-rov-software-photogrammetry-backend-1 bash -c "
mkdir -p /app/data/uploads/$JOB
cd /app/data/uploads/$JOB
for i in \$(seq $START_INDEX $END_INDEX); do
    printf 'Downloading GPAA%s.JPG... ' \$i
    curl -sL -o GPAA\${i}.JPG '$BASE_URL/GPAA'\${i}'.JPG'
    echo 'done'
done
echo ''
echo \"Downloaded \$(ls *.JPG | wc -l) images (\$(du -sh . | cut -f1))\"
"

# Update job status so pipeline knows images are ready
docker exec team-bath-rov-software-photogrammetry-backend-1 python3 -c "
from app.services.job_manager import job_manager
from app.models.job import JobStatus
job_manager.update_job('$JOB', status=JobStatus.PENDING)
print('Job status set to PENDING')
"

# Start pipeline
echo ""
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
