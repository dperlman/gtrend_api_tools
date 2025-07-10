import applescript

def close_safari_tab() -> None:
    """
    Close the first tab of the first Safari window using AppleScript.
    """
    script = '''
    tell application "Safari"
        activate
        if (count of every tab of window 1) > 1 then
            set current_tab_index to index of current tab of window 1
            display dialog "tab index: " & current_tab_index
            close every tab of window 1
        end if
    end tell
    return "success"
    '''
    result = applescript.run(script)
    print(f"Result.err: {result.err}")
    print(f"Result.code: {result.code}")
    print(f"Result.out: {result.out}")
    if result.code != 0:
        print(f"Error closing Safari tab: {result.err}")

if __name__ == "__main__":
    close_safari_tab()

# close tab current_tab_index of window 1