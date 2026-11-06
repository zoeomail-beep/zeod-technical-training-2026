#!/bin/bash
# Read-only macOS file and server audit. Does not change inspected files.
set -u
OUT="$HOME/Desktop/Mac_File_Audit_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"
ROOTS=("$HOME" "/Users/Shared/Server")
if [ ! -d /Users/Shared/Server ]; then ROOTS=("$HOME"); fi
printf 'Audit created: %s\nRoots: %s\n' "$(date)" "${ROOTS[*]}" > "$OUT/summary.txt"
df -h "$HOME" >> "$OUT/summary.txt" 2>&1
printf '\nServer share status:\n' >> "$OUT/summary.txt"
sharing -l >> "$OUT/summary.txt" 2>&1 || true
printf '\nFile counts by extension:\n' >> "$OUT/summary.txt"
find "${ROOTS[@]}" -type f -print 2>"$OUT/find_errors.txt" | awk -F/ '{n=$NF; if(n ~ /\./){sub(/^.*\./,"",n); print tolower(n)}else print "[none]"}' | sort | uniq -c | sort -nr | head -80 >> "$OUT/summary.txt"
find "${ROOTS[@]}" -type f -size 0 -print 2>/dev/null | head -5000 > "$OUT/zero_byte_files.txt"
find "${ROOTS[@]}" -type f ! -readable -print 2>/dev/null | head -5000 > "$OUT/unreadable_files.txt"
find "${ROOTS[@]}" -type d ! -readable -print 2>/dev/null | head -5000 > "$OUT/unreadable_folders.txt"
find "${ROOTS[@]}" -type f \( -iname '*.zip' -o -iname '*.ZIP' \) -print0 2>/dev/null | while IFS= read -r -d '' f; do
 if unzip -tqq "$f" >/dev/null 2>&1; then printf 'OK\t%s\n' "$f"; else printf 'FAILED\t%s\n' "$f"; fi
done > "$OUT/zip_tests.txt"
find "${ROOTS[@]}" -type f \( -iname '*.icloud' -o -iname '*.download' -o -iname '*.part' \) -print 2>/dev/null | head -5000 > "$OUT/potential_placeholders.txt"
find "${ROOTS[@]}" -type f -size +1024M -print 2>/dev/null | head -5000 > "$OUT/large_files.txt"
printf '\nZIP test summary:\n' >> "$OUT/summary.txt"
awk -F '\t' '{count[$1]++}END{for(k in count) print k,count[k]}' "$OUT/zip_tests.txt" >> "$OUT/summary.txt"
printf '\nNote: This is a preliminary audit, not a full filesystem integrity check. Duplicate hashing and all-file content verification are not performed.\n' >> "$OUT/summary.txt"
cd "$HOME/Desktop" && /usr/bin/zip -qr "$(basename "$OUT").zip" "$(basename "$OUT")"
printf '\nReport: %s.zip\n' "$OUT"
