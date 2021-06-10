*********
Changelog
*********

v0.2.3 (2021-05-04)
========================================

New features:

- Auto save: Save the state not just when Mopidy shuts down, but at
  (configurable) events. To reduce stress on a SD card, a save interval can be
  configured.

Bugs:

- Fix the section name for the example of the ini file shown in the
  README.md file. (Fixes #5)


v0.2.2 (2021-04-13)
========================================

Bugs:

- No double encoding of uris. (Fixes first issue in #3)

Improvements:

- Sometimes tracks cannot be loaded into the tracklist. The URIs of these
  tracks are now logged with a warning message mentioning possible reasons.
  it also plays the next available track. (Fixes second issue in #3)
- Remvove "Autoplay: " from log messages.


v0.2.1 (2020-10-26)
========================================

Bugs:

- 'Playback stopped' now stops.

Improvements:

- README.rst mentions possible conflict with ``core/restore_state = true``.
- README.rst mentions possible problems, if backends needs longer to
  initialize.
- README.rst explains that by using the ``File`` extension (URI starts with
  ``file://``) you can load any file permission permitted.


v0.2.0 (2020-10-16)
========================================

New features:

- Playlists can be specified in ``autostart/tracklist.uris`` with e.g.
  ``m3u://``. The items of the playlist are inserted into the tracklist in
  the position, where the playlist entry occurs. The playlist scheme specified
  must be supported by Mopidy.
- Glob patterns can now be specified in ``autostart/tracklist.uris`` for
  ``file://`` URIs to insert many files into the tracklist. The URI is
  ``match:file://`` followed by the file pattern, e.g.
  ``match:file:///usr/share/sounds/alsa/*.wav``. The ``File`` extension must be
  enabled. (Bug #1)

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
