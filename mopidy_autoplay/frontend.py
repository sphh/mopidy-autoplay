"""Autoplay extension for Mopidy.

A Mopidy extension to automatically pick up where you left off and start
playing the last track from the position before Mopidy was shut down.
"""

import logging
import pathlib
import glob
import urllib.parse
import json
import pykka

from mopidy import core
from . import Extension, Recollection


logger = logging.getLogger(__name__)


class AutoplayFrontend(pykka.ThreadingActor, core.CoreListener):
    """Autoplay's frontend implementation."""

    def __init__(self, config, core):
        """Initialize the `AutoplayFrontend` class."""
        logger.debug(
            "Autoplay: __init__(%s, %s)",
            config, core)

        super(AutoplayFrontend, self).__init__()
        self.core = core
        self.config = config[Extension.ext_name]

        # State file
        data_dir = Extension.get_data_dir(config)
        self.statefile = pathlib.Path(data_dir) / 'autoplay.state'
        logger.debug(
            "Autoplay: Use '%s' as statefile.",
            self.statefile)

    # The frontend implementation

    def on_start(self):                                         # noqa: D401
        """Called, when the extension is started."""
        logger.debug("Autoplay: on_start()")

        state = self.read_state(self.statefile)
        if state:
            self.restore_state(state)

    def on_stop(self):                                          # noqa: D401
        """Called, when the extension is stopped."""
        logger.debug("Autoplay: on_stop()")

        state = self.store_state()
        self.write_state(state, self.statefile)

    # Helper functions

    def _get_config(self, state, controller, option):
        """
        Return the configuration from `config` and `state`.

        If the extension's configuration has a value other than "auto" (which
        is translated into the class `Recollection`), return this value,
        otherwise the saved value from the state variable.

        Args:
            state (dict):
                A dictionary with the states saved for the 'tracklist',
                'mixer' and 'playback' controllers.
            controller (str):
                The controller name.
            option (str):
                The option name.

        Returns:
            value:
                The configuration or state value.

        """
        config = self.config.get(f'{controller}.{option}', Recollection)
        if config is Recollection:
            s = state.get(controller, {}).get(option, None)
        else:
            s = config
        logger.debug(
            "Autoplay: _get_config(%s, %s, %s) = %s",
            state, controller, option, s)
        return s

    def _set_option(self, state, controller, option):
        """
        Set the state to the controller's option.

        Args:
            state (TYPE):
                A dictionary with the states saved for the 'tracklist',
                'mixer' and 'playback' controllers.
            controller (str):
                The controller name.
            option (str):
                The option name.

        Returns:
            None.

        """
        logger.debug(
            "Autoplay: _set_option(%s, %s, %s)",
            state, controller, option)

        # Get value to be set
        value = self._get_config(state, controller, option)
        if value is None:
            return

        # Get method to be used to set option
        setter = getattr(getattr(self.core, controller), f'set_{option}')

        # Set value (and log message, if failed)
        if not setter(value):
            logger.info(
                "Autoplay: Set %s/%s to '%s' failed.",
                controller, option, value)

    # Worker functions

    def restore_state(self, state):
        """
        Restore the saved state.

        Args:
            state (dict):
                A dictionary with the states saved for the 'tracklist',
                'mixer' and 'playback' controllers.

        Returns:
            None.

        """
        # Reset tracklist
        tlid = None
        
        playlist_schemes = tuple(self.core.playlists.get_uri_schemes().get())
        uris = []
        for uri in self._get_config(state, 'tracklist', 'uris'):
            if uri.startswith('match:'):
                match = uri.split('match:', 1)[1]
                if match.startswith('file://'):
                    # Add files to the list of URIs using the match as glob
                    # pattern
                    uris.extend(
                        [f'file://{urllib.parse.quote(f)}'
                         for f in glob.glob(match[len('file://'):])])
                else:
                    logger.warning(
                        "Matching for URI %s not supported: %s",
                        match, uri)
            elif uri.startswith(playlist_schemes):
                # Add contents of known playlists to the list of URIs
                uris.extend(
                    [track.uri
                     for track
                     in self.core.playlists.get_items(uri).get() or []])
            elif '://' in uri:
                scheme, location = uri.split('://', 1)
                uris.append(f'{scheme}://{urllib.parse.quote(location)}')
            else:
                uris.append(uri)

        if uris:
            # Clear tracklist and add URIs
            self.core.tracklist.clear()
            self.core.tracklist.add(uris=uris)
            # Switch to specified index
            index = self._get_config(state, 'tracklist', 'index') or 0
            try:
                tlid = self.core.tracklist.get_tl_tracks().get()[index].tlid
            except Exception as e:
                logger.warning(
                    "Autoplay: Could not get tracklist index %s: %s",
                    index, e)
                tlid = None
        self._set_option(state, 'tracklist', 'consume')
        self._set_option(state, 'tracklist', 'random')
        self._set_option(state, 'tracklist', 'repeat')
        self._set_option(state, 'tracklist', 'single')

        # Reset mixer
        self._set_option(state, 'mixer', 'mute')
        self._set_option(state, 'mixer', 'volume')

        # Reset playback state
        if tlid is not None:
            # Why does this not work?
            #   self._set_option(state, 'playback', 'state')
            playback = self._get_config(state, 'playback', 'state')
            if playback == 'stopped':
                self.core.playback.stop()
            elif playback == 'playing':
                self.core.playback.play(tlid=tlid)
            elif playback == 'paused':
                self.core.playback.pause()
            time_position = self._get_config(state, 'playback', 'time_position')
            if time_position is not None:
                self.core.playback.seek(time_position)

    def store_state(self):
        """
        Assemble and return the state.

        Returns:
            state (dict):
                A dictionary with the states saved for the 'tracklist',
                'mixer' and 'playback' controllers.

        """
        # Initialize 'state' variable
        state = {
            'tracklist': {},
            'mixer': {},
            'playback': {},
            }

        # Tracks in tracklist
        tracklist = self.core.tracklist
        state['tracklist']['uris'] = [
            t.uri
            for t in tracklist.get_tracks().get()
            if t is not None]
        # Get currently playing track (or None)
        state['tracklist']['index'] = tracklist.index().get()
        # Get options
        state['tracklist']['consume'] = tracklist.get_consume().get()
        state['tracklist']['random'] = tracklist.get_random().get()
        state['tracklist']['repeat'] = tracklist.get_repeat().get()
        state['tracklist']['single'] = tracklist.get_single().get()

        # Get the mixer state
        mixer = self.core.mixer
        # True, False or None
        state['mixer']['mute'] = mixer.get_mute().get()
        # [0..100] or None
        state['mixer']['volume'] = mixer.get_volume().get()

        # Get the playback state
        playback = self.core.playback
        # Returns "stopped", "playing" or "paused"
        state['playback']['state'] = playback.get_state().get()
        state['playback']['time_position'] = playback.get_time_position().get()

        return state

    def read_state(self, file):
        """
        Read the state from the a json file.

        Args:
            file (str|Path):
                A json-formated file with the state dictionary.

        Returns:
            state (dict):
                A dictionary with the states saved for the 'tracklist',
                'mixer' and 'playback' controllers.

        """
        try:
            with open(file, 'r') as f:
                state = json.load(f)
        except IOError as e:
            logger.warning(
                "Autoplay: No state restored, "
                "because there was a problem opening the state file '%s': %s",
                file, e)
            return
        except json.JSONDecodeError as e:
            logger.error(
                "Autoplay: Error reading state from file '%s': %s",
                file, e)
            return
        else:
            logger.debug(
                "Autoplay: State read from file '%s'.",
                file)

        return state

    def write_state(self, state, file):
        """
        Write the state to a json file.

        Args:
            state (dict):
                A dictionary with the states saved for the 'tracklist',
                'mixer' and 'playback' controllers.
            file (str|Path):
                A writeable file.

        Returns:
            None.

        """
        try:
            with open(file, 'w') as f:
                json.dump(state, f)
        except IOError as e:
            logger.error(
                "Autoplay: Cannot open state file '%s' for writing: %s",
                file, e)
        except Exception as e:
            logger.error(
                "Autoplay: Problem saving state to file '%s': %s",
                file, e)
            logger.debug(
                "Autoplay: State: %s",
                state)
        else:
            logger.debug(
                "Autoplay: State written to file '%s'.",
                file)
