#!/bin/bash
# probe_umami.sh -- read-only reconnaissance of the Umami Mac app on this machine.
#
# Answers the one question that cannot be answered remotely: does Umami keep a
# local database we can read directly (fully automated refresh), or is the
# official export the only way in (one manual tap per refresh)?
#
# STRICTLY READ-ONLY. It never writes to, deletes from, or opens for writing
# anything belonging to the app. SQLite stores are copied to a scratch folder
# and inspected there, so the app's live files and WAL journals are untouched.
#
#   bash probe_umami.sh              # human-readable report
#   bash probe_umami.sh > report.txt # capture it to send on
#
# If sections come back "Operation not permitted", grant Full Disk Access to
# your terminal: System Settings > Privacy & Security > Full Disk Access.

set -uo pipefail

SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/umami-probe.XXXXXX")"
trap 'rm -rf "$SCRATCH"' EXIT

hr()  { printf '\n%s\n' "------------------------------------------------------------"; }
sec() { hr; printf '## %s\n\n' "$1"; }
note() { printf '   %s\n' "$1"; }

printf 'Umami local-access probe\n'
printf 'run at: %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
printf 'macOS : %s (%s)\n' "$(sw_vers -productVersion 2>/dev/null)" "$(uname -m)"

# ---------------------------------------------------------------- app bundle
sec "1. Application bundle"

APPS=()
while IFS= read -r line; do [ -n "$line" ] && APPS+=("$line"); done < <(
  {
    mdfind "kMDItemContentType == 'com.apple.application-bundle' && kMDItemFSName == '*mami*'" 2>/dev/null
    mdfind "kMDItemCFBundleIdentifier == '*umami*'c" 2>/dev/null
    ls -d /Applications/Umami.app "$HOME/Applications/Umami.app" 2>/dev/null
  } | sort -u
)

if [ ${#APPS[@]} -eq 0 ]; then
  note "Umami.app not found by Spotlight or in /Applications."
  note "If it is installed elsewhere, re-run as: UMAMI_APP=/path/to/Umami.app bash probe_umami.sh"
fi
[ -n "${UMAMI_APP:-}" ] && APPS=("$UMAMI_APP")

BUNDLE_IDS=()
for app in "${APPS[@]:-}"; do
  [ -n "$app" ] && [ -d "$app" ] || continue
  plist="$app/Contents/Info.plist"
  [ -f "$plist" ] || plist="$app/Info.plist"
  bid="$(defaults read "${plist%.plist}" CFBundleIdentifier 2>/dev/null)"
  ver="$(defaults read "${plist%.plist}" CFBundleShortVersionString 2>/dev/null)"
  printf '   app        : %s\n' "$app"
  printf '   bundle id  : %s\n' "${bid:-<unreadable>}"
  printf '   version    : %s\n' "${ver:-?}"
  [ -n "$bid" ] && BUNDLE_IDS+=("$bid")

  # iOS-app-on-Mac / Catalyst builds store data differently from AppKit builds.
  if /usr/libexec/PlistBuddy -c "Print :LSRequiresIPhoneOS" "$plist" >/dev/null 2>&1; then
    note "kind       : iOS app running on Apple silicon (data lives under Containers)"
  elif /usr/libexec/PlistBuddy -c "Print :UIDeviceFamily" "$plist" >/dev/null 2>&1; then
    note "kind       : Mac Catalyst"
  else
    note "kind       : native macOS build"
  fi

  # A URL scheme means we may be able to deep-link into a recipe from a plan.
  schemes="$(/usr/libexec/PlistBuddy -c "Print :CFBundleURLTypes" "$plist" 2>/dev/null |
             grep -Eo '[A-Za-z0-9.+-]+' | grep -vE '^(Dict|Array|CFBundle|URLTypes|URLSchemes|URLName)' | sort -u | tr '\n' ' ')"
  printf '   url schemes: %s\n' "${schemes:-none declared}"

  # AppIntents metadata == the app publishes Shortcuts actions we could script.
  if find "$app" -name 'Metadata.appintents' -maxdepth 4 2>/dev/null | grep -q .; then
    note "shortcuts  : YES - app ships AppIntents metadata (scriptable via 'shortcuts run')"
  else
    note "shortcuts  : no AppIntents metadata found in the bundle"
  fi
  printf '   sandboxed  : '
  if codesign -d --entitlements - --xml "$app" 2>/dev/null | grep -q 'app-sandbox'; then
    echo "yes (data confined to ~/Library/Containers/<bundle id>)"
  else
    echo "no / undetermined"
  fi
done

# Fall back to guesses so the rest of the probe still runs.
if [ ${#BUNDLE_IDS[@]} -eq 0 ]; then
  BUNDLE_IDS=("app.umami.umami" "com.strangequark.umami" "recipes.umami.umami")
  note "Guessing bundle ids for the search below: ${BUNDLE_IDS[*]}"
fi

# ------------------------------------------------------------- data location
sec "2. Where the data lives"

CANDIDATE_DIRS=()
for bid in "${BUNDLE_IDS[@]}"; do
  CANDIDATE_DIRS+=("$HOME/Library/Containers/$bid/Data/Library/Application Support")
  CANDIDATE_DIRS+=("$HOME/Library/Containers/$bid/Data/Documents")
  CANDIDATE_DIRS+=("$HOME/Library/Containers/$bid/Data/Library/Caches")
done
while IFS= read -r d; do CANDIDATE_DIRS+=("$d"); done < <(
  {
    ls -d "$HOME/Library/Group Containers/"*[Uu]mami* 2>/dev/null
    ls -d "$HOME/Library/Application Support/"*[Uu]mami* 2>/dev/null
    ls -d "$HOME/Library/Containers/"*[Uu]mami*/Data 2>/dev/null
  } | sort -u
)

FOUND_DIRS=()
for dir in "${CANDIDATE_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    FOUND_DIRS+=("$dir")
    size="$(du -sh "$dir" 2>/dev/null | cut -f1)"
    printf '   [found] %s  (%s)\n' "$dir" "${size:-?}"
  fi
done
if [ ${#FOUND_DIRS[@]} -eq 0 ]; then
  note "No Umami data directories readable."
  note "Either the app is not installed, or your terminal lacks Full Disk Access."
fi

# ------------------------------------------------------------- data files
sec "3. Candidate data files"

STORES=()
for dir in "${FOUND_DIRS[@]:-}"; do
  [ -n "$dir" ] || continue
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    kind="$(file -b "$f" 2>/dev/null | cut -c1-60)"
    size="$(du -h "$f" 2>/dev/null | cut -f1)"
    printf '   %-6s %-42s %s\n' "$size" "$(basename "$f")" "$kind"
    printf '          %s\n' "$f"
    case "$kind" in *SQLite*) STORES+=("$f") ;; esac
    case "$f" in *.realm) STORES+=("$f") ;; esac
  done < <(find "$dir" -type f \
             \( -name '*.sqlite' -o -name '*.db' -o -name '*.sqlite3' \
                -o -name '*.store' -o -name '*.realm' -o -name '*.json' \
                -o -name '*.binarypb' -o -name '*.data' \) \
             -size +1k 2>/dev/null | head -40)
done
[ ${#STORES[@]} -eq 0 ] && note "(no SQLite/Realm stores found in the directories above)"

# ------------------------------------------------------------- schema dump
sec "4. Schema of any SQLite store (read from a copy)"

for store in "${STORES[@]:-}"; do
  [ -n "$store" ] || continue
  case "$store" in *.realm)
      printf '\n   %s\n' "$store"
      note "Realm database. Not readable with stock tooling - needs the realm SDK."
      continue ;;
  esac
  base="$(basename "$store")"
  copy="$SCRATCH/$base"
  cp "$store" "$copy" 2>/dev/null || { note "could not copy $store"; continue; }
  # WAL/SHM carry recent writes; copy them so the snapshot is consistent.
  for ext in -wal -shm; do
    [ -f "${store}${ext}" ] && cp "${store}${ext}" "${copy}${ext}" 2>/dev/null
  done
  printf '\n   %s\n' "$store"
  tables="$(sqlite3 "$copy" ".tables" 2>/dev/null)"
  if [ -z "$tables" ]; then
    note "unreadable as SQLite (encrypted, or permission denied)"
    continue
  fi
  printf '   tables: %s\n\n' "$(echo "$tables" | tr -s ' \n' ' ')"
  echo "$tables" | tr -s ' ' '\n' | grep -v '^$' | while read -r t; do
    n="$(sqlite3 "$copy" "SELECT COUNT(*) FROM \"$t\";" 2>/dev/null)"
    printf '     %8s rows  %s\n' "${n:-?}" "$t"
  done
  if echo "$tables" | grep -qiE 'ZRECIPE|Z_PRIMARYKEY'; then
    note ""
    note ">> Core Data store detected. Columns on the recipe entity:"
    zt="$(echo "$tables" | tr -s ' ' '\n' | grep -iE '^ZRECIPE' | head -1)"
    [ -n "$zt" ] && sqlite3 "$copy" "PRAGMA table_info(\"$zt\");" 2>/dev/null |
      awk -F'|' '{printf "        %-34s %s\n", $2, $3}'
  fi
  if echo "$tables" | grep -qiE 'ACHANGE|ATRANSACTION'; then
    note ">> NSPersistentCloudKitContainer mirroring present (iCloud-synced Core Data)."
  fi
done

# ------------------------------------------------------------- integrations
sec "5. Automation surfaces"

printf '   Shortcuts app actions provided by Umami:\n'
if command -v shortcuts >/dev/null 2>&1; then
  note "'shortcuts' CLI present - it can run a shortcut, but cannot list app actions."
  note "Check by hand: open Shortcuts.app and search the action library for 'Umami'."
else
  note "'shortcuts' CLI not available on this macOS version."
fi
printf '\n   App extensions registered:\n'
pluginkit -mAvv 2>/dev/null | grep -i umami | sed 's/^/     /' || note "(none)"

printf '\n   Registered URL handlers:\n'
for bid in "${BUNDLE_IDS[@]}"; do
  /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
    -dump 2>/dev/null | grep -A2 -i "$bid" | grep -i 'bindings:' | head -3 | sed 's/^/     /'
done

# ------------------------------------------------------------- verdict
sec "6. Verdict"

if [ ${#STORES[@]} -gt 0 ]; then
  echo "   A local store exists. If section 4 shows recipe-shaped tables with"
  echo "   sensible row counts, PATH B (direct read) is viable: a script can"
  echo "   snapshot and query it with zero manual steps."
else
  echo "   No readable local store surfaced. PATH A (official export) is the"
  echo "   route: Account > 'Export all recipe books' > Recipe JSON Schema,"
  echo "   then run umami_ingest.py over the result."
fi
echo
echo "   Either way, send this whole report back and the ingest side can be"
echo "   pointed at whichever store or export actually exists."
hr
