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

**Notice**

There are some similar extensions which might suite you better:

- If you want to automatically play a playlist after start of the Mopidy
  service, use
  `Mopidy-DefaultPlaylist <https://pypi.org/project/Mopidy-DefaultPlaylist/>`_.
- If you want to automate music playback based on the time of the day, use
  `Mopidy-Auto <https://pypi.org/project/Mopidy-Auto/>`_.
- If you want to save the current playback state to be able to resume later,
  have a look at
  `Mopidy-Bookmarks <https://pypi.org/project/Mopidy-Bookmarks/>`_.


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


Project resources
=================

- `Source code <https://github.com/sphh/mopidy-autoplay>`_
- `Issue tracker <https://github.com/sphh/mopidy-autoplay/issues>`_
- `Changelog <https://github.com/sphh/mopidy-autoplay/blob/master/CHANGELOG.rst>`_


Credits
=======

- Original author: `Stephan Helma <https://github.com/sphh>`__
- Current maintainer: `Stephan Helma <https://github.com/sphh>`__
- `Contributors <https://github.com/sphh/mopidy-autoplay/graphs/contributors>`_
