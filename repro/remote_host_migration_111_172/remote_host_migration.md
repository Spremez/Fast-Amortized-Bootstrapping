# Remote Host Migration: delld@192.168.107.220 → luck@192.168.111.172

Date: 2026-08-24

## Status

| Item | Old host | New host |
|---|---|---|
| user@host | delld@192.168.107.220 (disconnected) | luck@192.168.111.172 |
| remote base | /home/delld/spz | /home/luck/spz |
| project task dir | /home/delld/spz/fab-* | /home/luck/spz/Fast-Amortized-Bootstrapping |
| port 22 reachability | — | reachable (verified 2026-08-24) |
| non-interactive auth | not configured (returncode=255) | verified 2026-08-24 (key auth OK) |

Completion log (2026-08-24):

- Public key installed into luck's `authorized_keys` (server state checked:
  home `drwxr-x---`, `~/.ssh` `700`, `authorized_keys` `600`, owner luck).
- Project uploaded to `/home/luck/spz/Fast-Amortized-Bootstrapping`:
  `git archive` of HEAD `53ca944` plus untracked docs/scripts/literature.
- Remote build verified: `make -j$(nproc)` on 104-thread Xeon Gold 6230R,
  Ubuntu 22.04 / gcc 11.4 — `main` ELF binary produced.

PowerShell pitfall (caused the first failed bootstrap attempt): PowerShell
does not treat `\` as a line continuation, so multi-line bash snippets pasted
into PowerShell split into broken commands. In PowerShell, run single-line
commands only, or use Git Bash. `ssh spz` works from PowerShell directly
(Windows OpenSSH reads the same `~/.ssh/config`).

Local machine changes already applied on 2026-08-24:

- Generated dedicated key pair (no passphrase, for non-interactive automation):
  - private: `~/.ssh/codex_luck_192_168_111_172`
  - public: `~/.ssh/codex_luck_192_168_111_172.pub`
  - fingerprint: `SHA256:GifiA4Lo/5nfuqbcMDnNOt0QtVqsW6AQkjnLS4CYCic`
- Rewrote `~/.ssh/config`: added `Host 192.168.111.172 spz` (User luck,
  IdentitiesOnly, dedicated IdentityFile) and deduplicated retired host blocks.
  `ssh spz` is now equivalent to `ssh luck@192.168.111.172`.
- Host key of 192.168.111.172 recorded in `~/.ssh/known_hosts` (ED25519).

## One-time bootstrap (requires luck's password once)

From the repo root in Git Bash:

```bash
bash repro/remote_host_migration_111_172/bootstrap_luck_172.sh
```

Equivalent single command:

```bash
cat ~/.ssh/codex_luck_192_168_111_172.pub | ssh luck@192.168.111.172 \
  "mkdir -p ~/.ssh ~/spz/Fast-Amortized-Bootstrapping && chmod 700 ~/.ssh && \
   cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo BOOTSTRAP_OK"
```

Expected output ends with `BOOTSTRAP_OK`, then the script verifies with a
non-interactive `ssh spz` (no password) printing `SSH_OK`.

## Uploading the current project into the task dir

```bash
ARCHIVE=/tmp/fab-head-$(git rev-parse --short HEAD).tar.gz
git archive --format=tar.gz --output "$ARCHIVE" HEAD
ssh spz "mkdir -p ~/spz/Fast-Amortized-Bootstrapping"
tar -cf - . | ssh spz "tar -xf - -C ~/spz/Fast-Amortized-Bootstrapping"
```

(The git-archive variant from stage214 keeps the remote clean of untracked files;
the tar variant includes local build state. Either works.)

## Directory layout (restructured 2026-08-27)

`~/spz` is the standalone base for all work of this project on the server:

```
/home/luck/spz/
├── fab-main/                        # CANONICAL main experiment environment (2026-08-27)
│                                    #   full git clone from bundle, main @ 6bea3a2,
│                                    #   local branches: main, candidate-sq-scale-sab,
│                                    #   candidate-d-lut-late-binding
│                                    #   build verified (gcc 11.4, -march=native),
│                                    #   scalar SAB smoke run: Pass (17.9 s)
├── bundles/fab-full-20260827.bundle # 7.6 MB all-refs git bundle (backup + re-clone source)
└── Fast-Amortized-Bootstrapping/    # legacy 2026-08-24 git-archive snapshot (no .git),
                                     #   kept read-only as the stage355 raw-output archive
```

Refresh procedure for `fab-main` (from the repo root in Git Bash):

```bash
git bundle create /tmp/fab.bundle --all
scp /tmp/fab.bundle spz:/tmp/
ssh spz "cd ~/spz/fab-main && git fetch /tmp/fab.bundle 'refs/heads/*:refs/remotes/origin/*' && git pull --ff-only"
```

## Routine usage after bootstrap

```bash
ssh spz                                   # login
ssh spz "ls ~/spz/fab-main"               # canonical experiment environment
scp local.file spz:~/spz/fab-main/
```

## Troubleshooting

- `Permission denied (publickey,password)` after bootstrap:
  - On the server check `ls -ld ~ ~/.ssh ~/.ssh/authorized_keys` →
    home must not be group-writable, `~/.ssh` 700, `authorized_keys` 600.
  - On CentOS/RHEL with SELinux enforcing: `restorecon -Rv ~/.ssh`.
  - On the client force the key: `ssh -i ~/.ssh/codex_luck_192_168_111_172 -o IdentitiesOnly=yes luck@192.168.111.172`.
- `REMOTE HOST IDENTIFICATION HAS CHANGED`: the server was re-imaged;
  `ssh-keygen -R 192.168.111.172` then reconnect.
- Windows OpenSSH (`C:\Windows\System32\OpenSSH`) reads the same
  `C:\Users\<user>\.ssh\config`, so VS Code Remote-SSH picks up host `spz` too.

## Security notes

- The private key never leaves this machine; only the `.pub` line is appended
  server-side. No passwords or keys are stored in this repository.
- The key has no passphrase so batch runs (make/CI-style handoffs) work
  non-interactively; protect the Windows account accordingly.
