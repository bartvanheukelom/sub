# sub
Curses client and utility commands for Subversion (SVN) on Linux (and probably Mac)

TortoiseSVN is great, but it's not available on Linux. There are various other clients, and I've tried some, but I always kept coming back to command-line `svn` because it's just more efficient.

Still, it can be quite inconvenient at times. That's why I created `sub`. It began as a set of additional utility commands to make certain tasks quicker to perform. Now, for the most part, `sub` consists of interactive `curses`-based UI, for e.g. browsing a repo, viewing a log and reviewing/committing local changes.

To install, clone or download anywhere and run `sub.py`. You could place it in your `PATH` (by symlinking it as `/usr/local/bin/sub`, for example) to make it easier to access. Note that `sub` does not include an SVN library, but instead uses the `svn` command installed on your system.

Run `sub help` for an overview of available commands.
