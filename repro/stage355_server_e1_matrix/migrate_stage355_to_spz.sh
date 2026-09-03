#!/usr/bin/env bash
# One-shot migration of the stage355 benchmark from ~/spz/... to /home/spz/...
# Preconditions (checked, fail-closed):
#   - /home/spz/Fast-Amortized-Bootstrapping-stage355-e1-server exists and is
#     writable by the ssh user (created via sudo by the operator).
#   - The resume-capable runner is present next to this script.
# The migration stops the running driver (the current ./main process may be
# killed; the perf-loop resume logic restarts from the first missing run),
# rsyncs the tree, and relaunches under nohup in the new location.
set -uo pipefail

OLD="$HOME/spz/Fast-Amortized-Bootstrapping-stage355-e1-server"
NEW="/home/spz/Fast-Amortized-Bootstrapping-stage355-e1-server"
STAGE_REL="repro/stage355_server_e1_matrix"

if [ ! -d "$NEW" ] || ! touch "$NEW/.wtest" 2>/dev/null; then
  echo "BLOCK: $NEW missing or not writable (run the sudo mkdir/chown first)" >&2
  exit 1
fi
rm -f "$NEW/.wtest"

echo "[1/5] stopping current driver"
pkill -f run_stage355_server_matrix.sh 2>/dev/null || true
# kill only ./main processes whose cwd is the OLD tree (shared server: never
# kill by process name alone)
for pid in $(pgrep -x main 2>/dev/null); do
  if [ "$(readlink -f /proc/$pid/cwd 2>/dev/null)" = "$OLD" ]; then
    kill "$pid" 2>/dev/null || true
  fi
done
sleep 3

echo "[2/5] rsync tree -> $NEW"
rsync -a --delete "$OLD/" "$NEW/"
# the tree still carries the pre-resume runner inside; replace with this dir's copy
cp "$NEW/$STAGE_REL/migrate_stage355_to_spz.sh" /dev/null 2>/dev/null || true

echo "[3/5] install resume-capable runner"
if [ -f "$NEW/$STAGE_REL/run_stage355_server_matrix.resume.sh" ]; then
  cp "$NEW/$STAGE_REL/run_stage355_server_matrix.resume.sh" "$NEW/$STAGE_REL/run_stage355_server_matrix.sh"
fi

echo "[4/5] fix ROOT path in the runner copy"
sed -i "s|^ROOT=.*|ROOT=\"$NEW\"|" "$NEW/$STAGE_REL/run_stage355_server_matrix.sh"

echo "[5/5] relaunch under nohup"
cd "$NEW" || exit 1
nohup bash "$STAGE_REL/run_stage355_server_matrix.sh" >> "$STAGE_REL/nohup.log" 2>&1 &
sleep 3
if pgrep -f run_stage355_server_matrix.sh >/dev/null; then
  echo "MIGRATED_AND_RUNNING (pid $(pgrep -f run_stage355_server_matrix.sh | head -1))"
  tail -3 "$NEW/$STAGE_REL/raw/driver.log"
else
  echo "BLOCK: relaunch failed; inspect $NEW/$STAGE_REL/nohup.log" >&2
  exit 1
fi
