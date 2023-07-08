on run argv
    tell application "Safari"
        activate
        open location "file://" & item 1 of argv & "#page=" & item 2 of argv
    end tell
end run