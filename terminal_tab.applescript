on run argv
    set commandText to item 1 of argv
    set profileName to item 2 of argv
    tell application "Terminal"
        if not (exists settings set profileName) then error "No existe el perfil de Terminal: " & profileName
        activate
        if (count of windows) is 0 then
            set targetTab to do script ""
        else
            set targetWindow to front window
            set miniaturized of targetWindow to false
            set visible of targetWindow to true
            set index of targetWindow to 1
            delay 0.3
            -- Algunas versiones representan las pestañas como ventanas en AppleScript.
            -- Capturamos las sesiones de todo Terminal por su TTY, no por ventana.
            set previousTTYs to {}
            repeat with existingWindow in windows
                repeat with existingTab in tabs of existingWindow
                    set end of previousTTYs to tty of existingTab
                end repeat
            end repeat
            set targetTitle to name of targetWindow
            tell application "System Events"
                tell process "Terminal"
                    set frontmost to true
                    perform action "AXRaise" of (first window whose name is targetTitle)
                    delay 0.3
                    keystroke "t" using {command down}
                end tell
            end tell
            set foundNewTab to false
            repeat 50 times
                delay 0.1
                set newTabs to {}
                set newTTYs to {}
                repeat with candidateWindow in windows
                    repeat with candidateTab in tabs of candidateWindow
                        set candidateTTY to tty of candidateTab
                        if candidateTTY is not "" and candidateTTY is not missing value and candidateTTY is not in previousTTYs and candidateTTY is not in newTTYs then
                            set end of newTabs to contents of candidateTab
                            set end of newTTYs to candidateTTY
                        end if
                    end repeat
                end repeat
                if (count of newTabs) > 1 then error "Se crearon varias sesiones a la vez; no se inició SSH. Intenta de nuevo sin abrir otras pestañas simultáneamente."
                if (count of newTabs) is 1 then
                    set targetTab to item 1 of newTabs
                    set foundNewTab to true
                    exit repeat
                end if
            end repeat
            if not foundNewTab then error "No se identificó la sesión nueva de Terminal; no se inició SSH."

        end if
        set current settings of targetTab to settings set profileName
        do script commandText in targetTab
    end tell
end run
