**tasknotify** produces desktop notifications using libnotify, even in
headless environments such as scripts run by cron.
It does this by looking for  the environment variables `DISPLAY` and
`DBUS_SESSION_BUS_ADDRESS` in other processes, likely from the current
desktop session, and setting them before calling libnotify.
This method is based on another program, [`notify-send-headless`][1],
provided by Peter Odding’s `proc` Python package.

[1]: https://proc.readthedocs.io/en/latest/api.html#module-proc.notify

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
history unless it comes with a valid desktop-entry hint—it has to know
what application the notification came from. To enable this, create a valid
desktop file in `~/.local/share/applications` for tasknotify, and name it
`tasknotify.desktop`.
Or, replace tasknotify with the app name from the `--app-name` argument
to save history on a per-application basis.

References:

- <https://docs.gtk.org/gio/class.Notification.html#description>
- <https://specifications.freedesktop.org/desktop-entry-spec/latest/>

# Requirements

- [libnotify](https://gitlab.gnome.org/GNOME/libnotify)
- [PyGObject](https://wiki.gnome.org/Projects/PyGObject)
- [psutils](https://github.com/rrthomas/psutils)

# Copyright

Copyright © 2025–2026 Dylan Maltby

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this software except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
