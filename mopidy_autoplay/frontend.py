"""Autoplay extension for Mopidy.

A Mopidy extension to automatically pick up where you left off and start
playing the last track from the position before Mopidy was shut down.
"""

import logging
import pathlib
import glob
import json
import threading
import queue
import time

import pykka

from mopidy import core
from . import Extension, Recollection


logger = logging.getLogger(__name__)


class Timer(threading.Thread):
    """Persistent timer."""

    def __init__(self, timeout, callback):
        """Initialize the `Timer` class."""
        super().__init__()
        self.timeout = timeout
        self.callback = callback
        # The queue to control the timer
        self.queue = queue.SimpleQueue()

    def set(self):
        """Set the timer."""
        self.queue.put(True)

    def stop(self):
        """Stop the thread."""
        self.queue.put(False)

    def run(self):
        """Run the thread."""
        while True:
            cmd = self.queue.get(block=True, timeout=None)
            if cmd:
                # Cool-down period
                time.sleep(self.timeout)
                # Empty the queue
                while not self.queue.empty():
                    self.queue.get(block=False)
                # Call the callback function
                self.callback()
            else:
                # Exit thread
                return


class AutoplayFrontend(pykka.ThreadingActor, core.CoreListener):
    """Autoplay's frontend implementation."""

    def __init__(self, config, core):
        """Initialize the `AutoplayFrontend` class."""
        logger.debug(
            "__init__(%s, %s)",
            config, core)

        super(AutoplayFrontend, self).__init__()
        self.core = core
        self.config = config[Extension.ext_name]

        # Persistent timer for save on events
        if self.config['save_on_events']:
            self.timer = Timer(self.config['save_interval'], self.save_state)
        else:
            self.timer = None

        # State file
        data_dir = Extension.get_data_dir(config)
        self.statefile = pathlib.Path(data_dir) / 'autoplay.state'
        logger.debug(
            "Use '%s' as statefile.",
            self.statefile)

    # The frontend implementation

    def on_start(self):                                         # noqa: D401
        """Called, when the extension is started."""
        logger.debug("on_start()")

        self.load_state()
        if self.timer:
            self.timer.start()

    def on_stop(self):                                          # noqa: D401
        """Called, when the extension is stopped."""
        logger.debug("on_stop()")

        if self.timer:
            self.timer.stop()
        self.save_state()

    def on_event(self, event, **kwargs):                        # noqa: D401
        """Called on all events."""
        logger.debug("on_event(%s, %s)", event, kwargs)

        if event in self.config['save_on_events']:
            self.timer.set()

    # Main functions

    def load_state(self):
        """Load the state from the disk."""
        logger.debug("load_state()")

        state = self.read_state(self.statefile)
        if state:
            self.restore_state(state)

        # Add required keys to the state dictionary
        if 'tracklist' not in state:
            state['tracklist'] = {}
        if 'mixer' not in state:
            state['mixer'] = {}
        if 'playback' not in state:
            state['playback'] = {}

        # Save a reference to the state dictionary, so that we do not have to
        # create it on every event, which would initiate a save.
        self._state = state

    def save_state(self):
        """Save the state to the disk."""
        logger.debug("save_state()")

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
            "_get_config(%s, %s, %s) = %s",
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
            "_set_option(%s, %s, %s)",
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
                "Set %s/%s to '%s' failed.",
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

        uris = []
        for uri in self._get_config(state, 'tracklist', 'uris'):
            if uri.startswith('match:'):
                match = uri.split('match:', 1)[1]
                if match.startswith('file://'):
                    # Add files to the list of URIs using the match as glob
                    # pattern
                    uris.extend(
                        [f'file://{f}'
                         for f in glob.glob(match[len('file://'):])])
                else:
                    logger.warning(
                        "Matching for URI %s not supported: %s",
                        match, uri)
            else:
                uris.append(uri)

        if uris:
            # Generate a list of track URIs from URIs
            track_uris = [
                track.uri
                for sublist in self.core.library.lookup(uris).get().values()
                for track in sublist]
            # Clear tracklist and add tracks
            self.core.tracklist.clear()
            self.core.tracklist.set_consume(False)
            self.core.tracklist.add(uris=track_uris)
            # Switch to specified index
            index = self._get_config(state, 'tracklist', 'index') or 0

            # We count the index, because we might have the same track more
            # than once in the tracklist
            tl_tracks = self.core.tracklist.get_tl_tracks().get()
            for i, uri in enumerate(track_uris):
                if tl_tracks:
                    track_uri = tl_tracks[0].track.uri
                else:
                    # Processed all available tracks, but there are still
                    # tracks, which were requested
                    track_uri = None
                if uri == track_uri:
                    if index == 0:
                        tlid = tl_tracks[0].tlid
                    tl_tracks.pop(0)
                    index -= 1
                else:
                    logger.warning(
                        "Tracklist %s loaded into tracklists, "
                        "but it cannot be found there! "
                        "Possible reasons are: "
                        "1. The track has disappeared.  "
                        "2. The backend '%s' does not exist.  "
                        "3. The backend '%s' is not ready (yet).",
                        uri, uri.split(':', 1)[0], uri.split(':', 1)[0])
                    if index != 0:
                        index -= 1

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
            if playback != 'stopped':
                time_position = self._get_config(
                    state, 'playback', 'time_position')
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
        # Get the state dictionary from our internal cache, so that we do not
        # have to recreate it
        state = self._state

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
                "No state restored, "
                "because there was a problem opening the state file '%s': %s",
                file, e)
            state = {}
        except json.JSONDecodeError as e:
            logger.error(
                "Error reading state from file '%s': %s",
                file, e)
            state = {}
        else:
            logger.debug(
                "State read from file '%s'.",
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
                "Cannot open state file '%s' for writing: %s",
                file, e)
        except Exception as e:
            logger.error(
                "Problem saving state to file '%s': %s",
                file, e)
            logger.debug(
                "State: %s",
                state)
        else:
            logger.debug(
                "State written to file '%s'.",
                file)
