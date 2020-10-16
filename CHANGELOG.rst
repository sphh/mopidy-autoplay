*********
Changelog
*********

v0.2.0 (2020-10-16)
========================================

New features:
- Playlists can be specified in ``autostart/tracklist.uris`` with e.g.
  ``m3u://``. The items of the playlist are inserted into the tracklist in
  the position, where the playlist entry occurs. The playlist scheme specified
  must be supported by Mopidy.
- Glob patterns can be specified in ``autostart/tracklist.uris`` to insert
  files into the tracklist. The URI is ``glob://`` followed by the file
  pattern, e.g. ``glob:///usr/share/sounds/alsa/*.wav``. The ``File`` extension
  must be enabled. (Bug #1)

Bugs:
- Index defaults always to 0. (If Mopidy is closed with nothing playing, no
  index could not be saved and so the default index after starting was none.)

Improvements:
- Mention 'core/restore_state' in README.rst.
- Add section "How to find the URIs?" to README.rst.


v0.1.1 (2020-09-16)
========================================

- Typo in README.rst corrected.


v0.1.0 (2020-09-16)
========================================

- Initial release.
