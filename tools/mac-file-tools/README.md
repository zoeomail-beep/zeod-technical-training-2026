# Mac file tools

Backup of the existing macOS Downloads sorter and file auditor, retrieved 7 November 2026. The source scripts are preserved unchanged.

## Downloads sorter

`downloads_sorter.py` previews eligible Downloads files by default. Files must have a Spotlight Date Added older than seven days and must not have been modified within 24 hours. Apply mode moves files; name collisions are skipped.

Preview on a MacBook with the server mounted:

```sh
python3 downloads_sorter.py --server /Volumes/Server
```

On the Mac mini, the original default server path is `/Users/Shared/Server`.

The saved sorter uses the older shared Media & Artwork routing. It has not yet been updated to the newer project-specific asset folders. Its duplicate protection checks destination filenames, not file contents. Review and update the routing before using `--apply`.

## File auditor

`mac_file_audit.sh` inspects the current user home and, when available, `/Users/Shared/Server`. It writes a report folder and ZIP on the Desktop. It reports extension counts, zero-byte and unreadable items, ZIP validation results, large files and potential placeholders. It does not hash duplicate files or verify every file's contents.

```sh
bash mac_file_audit.sh
```

Reports may contain private filenames and system information. Audit outputs, personal files, credentials and machine-specific scheduling settings are excluded from this backup.
