# Stage214 SSH Handoff Commands

These commands intentionally do not contain credentials. Use an SSH agent or
interactive credential entry outside committed artifacts.

```bash
REMOTE=delld@192.168.107.220
REMOTE_BASE=/home/delld/spz
ARCHIVE=/tmp/fab-stage214-$(git rev-parse --short HEAD).tar.gz

git archive --format=tar.gz --output "$ARCHIVE" HEAD
ssh "$REMOTE" "mkdir -p $REMOTE_BASE/fab-stage214 && tar -xzf - -C $REMOTE_BASE/fab-stage214" < "$ARCHIVE"
ssh "$REMOTE" "cd $REMOTE_BASE/fab-stage214 && bash repro/stage214_frontier_native_counter_handoff/run_native_stage214_counters.sh"
scp -r "$REMOTE:$REMOTE_BASE/fab-stage214/repro/stage214_frontier_native_counter_handoff/native_perf_raw" repro/stage214_frontier_native_counter_handoff/
```
