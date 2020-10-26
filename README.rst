****************************
Mopidy-Autoplay
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-Autoplay
    :target: https://pypi.org/project/Mopidy-Autoplay/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/circleci/build/gh/sphh/mopidy-autoplay
    :target: https://circleci.com/gh/sphh/mopidy-autoplay
    :alt: CircleCI build status

.. image:: https://img.shields.io/codecov/c/gh/sphh/mopidy-autoplay
    :target: https://codecov.io/gh/sphh/mopidy-autoplay
    :alt: Test coverage

Mopidy extension to automatically pick up where you left off and start playing
the last track from the position before Mopidy was shut down.

If you simply want to restore Mopidy's state exactly as it were when you left,
you can set
`core/restore_state <https://docs.mopidy.com/en/latest/config/#confval-core-restore_state>`_.
to ``true``. The default behaviour of this extension is to mimick this, but by
using this extension, you can modify the state. You can set the entries in the
tracklist, the tracklist options, the playback state (e.g. set it to
``paused``) and the mixer's volume (and mute state).

**Notice**

There are some similar extensions which might suit your requirements better:

- If you want to automatically play a playlist after start of the Mopidy
  service, use
  `Mopidy-DefaultPlaylist <https://pypi.org/project/Mopidy-DefaultPlaylist/>`_.
- If you want to automate music playback based on the time of the day, use
  `Mopidy-Auto <https://pypi.org/project/Mopidy-Auto/>`_.
- If you want to save the current playback state to be able to resume later,
  have a look at
  `Mopidy-Bookmarks <https://pypi.org/project/Mopidy-Bookmarks/>`_.

**Caveats**

- If this extension tries to play tracks from backends, that have not finished
  initialising, the playing might fail. For a discussion see this
  `topic <https://discourse.mopidy.com/t/restore-state-not-working-for-dlna-extension/4358>`_.
- If you set Mopidy's configuration option ``core/restore_state = true``, this
  might interfere with Mopidy-Autoplay, so it is best to either set
  ``core/restore_state = false`` or delete this entry. (When I tested it,
  Mopidy-Autoplay gets activated well after the state is restored with
  ``core/restore_state``, thus Mopidy-Autoplay takes precedence.)


Installation
============

Install by running::

    python3 -m pip install Mopidy-Autoplay

See https://mopidy.com/ext/mopidy-autoplay/ for alternative installation methods.


Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-Autoplay to your Mopidy configuration file::

    [mopidy-autoplay]
    enabled = true

    # Each of the following keys can take the value "auto" (without quotes),
    # in which case the values active before Mopidy was stopped are used.

    # Tracklist (uris = uri, ...; index = int)
    tracklist.uris = auto
    tracklist.index = auto

    # Tracklist options (on|off|true|false)
    tracklist.consume = auto
    tracklist.random = auto
    tracklist.repeat = auto
    tracklist.single = auto

    # Playback (state = stopped|playing|paused; time_position = [in ms])
    playback.state = auto
    playback.time_position = auto

    # Mixer (volume = [0..100]; mute = on|off|true|false)
    mixer.volume = auto
    mixer.mute = auto

With this default configuration, Mopidy restores the queue (tracklist) with
all the tracks from the time it was shut down. It restores all the settings,
such as "consume", "random", "repeat" and "single", sets the volume level and
if it was muted and finally plays the track at the position mopidy was playing
before it was shut down.

If you always want to play the last track, regardless if it was playing or
muted before shutdown, use::

    playback.state = playing
    mixer.volume = 80
    mixer.mute = off

If you always want to start with the same track, e.g. a webradio stream, add
to the settings above::

    tracklist.uris = http://icecast.radiofrance.fr/fip-hifi.aac
    tracklist.index = 0

For more than one track, separate them with a comma ``,``. Please also note,
that the URI is not encapsulated in quotation marks (``"`` or ``'``).

**How to find the URIs?**

You can use any of the URIs supported on your installation of Mopidy. Here are
some examples:

- ``file:///usr/share/sounds/alsa/Noise.wav`` (Extension
  `Mopidy-File <https://docs.mopidy.com/en/latest/ext/file/>`_ must be enabled,
  which it is by default) Please note, that as of Mopidy version 3.0.2, it is
  possible to load any file on the filesystem permission permitted, but that
  might change in future to just allow files from directories mentioned in
  ```file/media_dirs`` <https://docs.mopidy.com/en/latest/ext/file/#confval-file/media_dirs>`_.
- ``http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio2_mf_p`` (Extension
  `Mopidy-Stream <https://docs.mopidy.com/en/latest/ext/stream/>`_ must be
  enabled, which it is by default)
- ``m3u://<myplaylist>.m3u8`` (Extension
  `Mopidy-M3U <https://docs.mopidy.com/en/latest/ext/m3u/>`_) must be enabled,
  which it is by default) – all entries of this playlist will be inserted into
  the list instead of ``m3u://``.

In addition to these URIs, which are supported natively by Mopidy,
Mopidy-Autoplay also supports a unique ``match:`` URI. Currently implemented
are `glob patterns <https://en.wikipedia.org/wiki/Glob_(programming)>`_ to
load many files from the file system, e.g. the URI will load all ``.wav``
files found in the directory ``/usr/share/sounds/alsa/``:

- ``match:file:///usr/share/sounds/alsa/*.wav`` (Extension
  `Mopidy-File <https://docs.mopidy.com/en/latest/ext/file/>`_) must be
  enabled, which it is by default) – all files found will be inserted into the
  list instead of ``match:file://``. Note, that according to
  `Python's documentation <https://docs.python.org/3/library/glob.html#glob.glob>`_,
  the order of the files is unpredictable and depends on the operating system.

If you don't know, how the URI is named, you can do the following:

1. Assemble the tracks, you want to play after start-up, put all of them into
   Mopidy's queue.
2. Stop Mopidy.
3. Open the state file ``/var/lib/mopidy/autoplay/autoplay.state`` and look for
   the ``tracklist/uris`` entry. This should be the list of URI you are looking
   for.
4. Copy this list into Mopidy's configuration file under
   ``autoplay/tracklist.uris``, remove the square brackets (``[``, ``]``) and
   the quotation marks (``"``) surrounding the URIs, keeping the commas (``,``)
   between the URIs, e.g.
   ``tracklist.uris = file:///usr/share/sounds/alsa/Noise.wav, http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio2_mf_p``.
5. Take also notice of the ``tracklist/index`` entry in the state file, which
   can be used as ``tracklist.index`` in the configuration file to start with
   a certain entry.


Project resources
=================

- `Source code <https://github.com/sphh/mopidy-autoplay>`_
- `Issue tracker <https://github.com/sphh/mopidy-autoplay/issues>`_
- `Changelog <https://github.com/sphh/mopidy-autoplay/blob/master/CHANGELOG.rst>`_


Credits
=======

- Original author: `Stephan Helma <https://github.com/sphh>`_
- Current maintainer: `Stephan Helma <https://github.com/sphh>`_
- `Contributors <https://github.com/sphh/mopidy-autoplay/graphs/contributors>`_
