"""Extension hook for 'AutoPlay' Mopidy extension."""

import logging
import pathlib

import pkg_resources

from mopidy import config, ext

__version__ = pkg_resources.get_distribution("Mopidy-Autoplay").version


logger = logging.getLogger(__name__)


class Recollection:
    """Marker for 'auto' configuration values."""

    pass


class AutoValue(config.ConfigValue):
    """Encapsulation of `ConfigValue` to enable a value of 'auto'."""

    def __init__(self, klass, *args, **kwargs):
        """Initialize the `AutoValue` class."""
        self._klass = klass(*args, **kwargs)

    def deserialize(self, value):
        """Cast raw string to appropriate type."""
        if value == 'auto':
            return Recollection
        else:
            return self._klass.deserialize(value)

    def serialize(self, value, display=False):
        """Convert value back to string for saving."""
        if value is Recollection:
            return 'auto'
        else:
            return self._klass.serialize(value, display=display)


class Extension(ext.Extension):
    """Autoplay Mopidy extension."""

    dist_name = "Mopidy-Autoplay"
    ext_name = "autoplay"
    version = __version__

    def get_default_config(self):
        """Return the extension's default config as a bytestring."""
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        """Return the extension's config valitation schema."""
        schema = super().get_config_schema()

        #
        # Tracklist
        #

        # uris = [uri, ...]|"auto"
        schema['tracklist.uris'] = AutoValue(config.List)
        # index = int|"auto"
        schema['tracklist.index'] = AutoValue(config.Integer, minimum=0)

        # Tracklist options (True|False|"auto")
        schema['tracklist.consume'] = AutoValue(config.Boolean)
        schema['tracklist.random'] = AutoValue(config.Boolean)
        schema['tracklist.repeat'] = AutoValue(config.Boolean)
        schema['tracklist.single'] = AutoValue(config.Boolean)

        #
        # Playback
        #

        # state = "stopped"|"playing"|"paused"|"auto"
        schema['playback.state'] = AutoValue(
            config.String, choices=['stopped', 'playing', 'paused'])
        # time_position = [ms]|"auto"
        schema['playback.time_position'] = AutoValue(
            config.Integer, minimum=0)

        #
        # Mixer
        #

        # volume = [0..100]|"auto"
        schema['mixer.volume'] = AutoValue(
            config.Integer, minimum=0, maximum=100)
        # mute = True|False|"auto")
        schema['mixer.mute'] = AutoValue(config.Boolean)

        return schema

    def setup(self, registry):
        """Register the extension's components in the extension `Registry`."""
        logger.info("%s %s", self.dist_name, self.version)

        from .frontend import AutoplayFrontend
        registry.add("frontend", AutoplayFrontend)
