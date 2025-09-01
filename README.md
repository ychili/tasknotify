**tasknotify** produces desktop notifications using libnotify, even in
headless environments such as scripts run by cron.
It does this by looking for  the environment variables `DISPLAY` and
`DBUS_SESSION_BUS_ADDRESS` in other processes, likely from the current
desktop session, and setting them before calling libnotify.

# Usage

    echo "Body." | tasknotify "Summary"
    # Notification is sent.
    echo "" | tasknotify "Summary"
    # Notification is not sent, because we only got whitespace on stdin.
    tasknotify "Summary" "Body."
    # Notification is sent, because some text was given as a BODY argument.

**tasknotify** will produce a desktop notification if significant text
(not just whitespace) is read from standard input or if a second positional
argument *BODY* is given. The first positional argument is the notification's
summary line.

For Plasma notifications at least, the notification will not be saved to
history unless it comes with a valid desktop-entry hint -- it has to know
what application the notification came from. To enable this, create a valid
desktop file in `~/.local/share/applications` for tasknotify, and name it
`tasknotify.desktop`.
Or, replace tasknotify with the app name from the `--app-name` argument
to save history on a per-application basis.

References:
    - <https://specifications.freedesktop.org/desktop-entry-spec/latest/>
    - <https://www.reddit.com/r/kde/comments/vo5am7/comment/ieaxehl/>

# Requirements

- libnotify
- PyGObject
- psutils
