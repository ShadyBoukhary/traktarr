import json
import os
import sys

from attrdict import AttrDict


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


class AttrConfig(AttrDict):
    """
    Simple AttrDict subclass to return None when requested attribute does not exist
    """

    def __init__(self, config):
        super().__init__(config)

    def __getattr__(self, item):
        try:
            return super().__getattr__(item)
        except AttributeError:
            pass
        # Default behaviour
        return None


class Config(object, metaclass=Singleton):
    base_config = {
        'core': {
            'debug': False
        },
        'notifications': {
            'verbose': True
        },
        'automatic': {
            'movies': {
                'intervals': {
                    'public_lists': 20,
                    'user_lists': 6
                },
                'anticipated': 3,
                'trending': 3,
                'popular': 3,
                'boxoffice': 10
            },
            'shows': {
                'intervals': {
                    'public_lists': 48,
                    'user_lists': 12
                },
                'anticipated': 10,
                'trending': 1,
                'popular': 1
            }
        },
        'filters': {
            'shows': {
                'disabled_for': [],
                'allowed_countries': [],
                'allowed_languages': [],
                'blacklisted_genres': [],
                'blacklisted_networks': [],
                'blacklisted_min_runtime': 15,
                'blacklisted_max_runtime': 0,
                'blacklisted_min_year': 2000,
                'blacklisted_max_year': 2019,
                'blacklisted_title_keywords': [],
                'blacklisted_tvdb_ids': [],
            },
            'movies': {
                'disabled_for': [],
                'allowed_countries': [],
                'allowed_languages': [],
                'blacklisted_genres': [],
                'blacklisted_min_runtime': 60,
                'blacklisted_max_runtime': 0,
                'blacklisted_min_year': 2000,
                'blacklisted_max_year': 2019,
                'blacklisted_title_keywords': [],
                'blacklisted_tmdb_ids': [],
                'rotten_tomatoes': ""
            }
        },
        'radarr': {
            'api_key': '',
            'minimum_availability': 'released',
            'quality': 'HD-1080p',
            'root_folder': '/movies/',
            'url': 'http://localhost:7878/'
        },
        'sonarr': {
            'api_key': '',
            'language': 'English',
            'quality': 'HD-1080p',
            'root_folder': '/tv/',
            'season_folder': True,
            'tags': [],
            'url': 'http://localhost:8989/'
        },
        'omdb': {
            'api_key': ''
        },
        'trakt': {
            'client_id': '',
            'client_secret': ''
        }
    }

    def __init__(self, configfile=None, cachefile=None, logfile=None):
        """Initializes config"""
        self.conf = None

        self.config_path = configfile or '/tmp/test_config.json'
        self.cache_path = cachefile or '/tmp/test_cache.db'
        self.log_path = logfile or '/tmp/test_activity.log'

    @property
    def cfg(self):
        # Return existing loaded config
        if self.conf:
            return self.conf

        # For testing - if config file doesn't exist, return base config
        if not os.path.exists(self.config_path):
            self.conf = AttrConfig(self.base_config)
            return self.conf

        # Built initial config if it doesn't exist
        if self.build_config():
            print("Please edit the default configuration before running again!")
            sys.exit(0)
        # Load config, upgrade if necessary
        else:
            tmp = self.load_config()
            self.conf, upgraded = self.upgrade_settings(tmp)

            # Save config if upgraded
            if upgraded:
                self.dump_config()
                print("New config options were added, adjust and restart!")
                sys.exit(0)

            return self.conf

    @property
    def cachefile(self):
        return self.cache_path

    @property
    def logfile(self):
        return self.log_path

    def build_config(self):
        if os.path.exists(self.config_path):
            return False
        print("Dumping default config to: %s" % self.config_path)
        with open(self.config_path, 'w') as fp:
            json.dump(self.base_config, fp, sort_keys=True, indent=2)
        return True

    def dump_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'w') as fp:
                json.dump(self.conf, fp, sort_keys=True, indent=2)
            return True
        else:
            return False

    def load_config(self):
        with open(self.config_path, 'r') as fp:
            return AttrConfig(json.load(fp))

    def __inner_upgrade(self, settings1, settings2, key=None, overwrite=False):
        sub_upgraded = False
        merged = settings2.copy()

        if isinstance(settings1, dict):
            for k, v in settings1.items():
                # missing k
                if k not in settings2:
                    merged[k] = v
                    sub_upgraded = True
                    if not key:
                        print("Added %r config option: %s" % (str(k), str(v)))
                    else:
                        print("Added %r to config option %r: %s" % (str(k), str(key), str(v)))
                    continue

                # iterate children
                if isinstance(v, (dict, list)):
                    merged[k], did_upgrade = self.__inner_upgrade(settings1[k], settings2[k], key=k,
                                                                  overwrite=overwrite)
                    sub_upgraded = did_upgrade or sub_upgraded
                elif settings1[k] != settings2[k] and overwrite:
                    merged = settings1
                    sub_upgraded = True
        elif isinstance(settings1, list) and key:
            for v in settings1:
                if v not in settings2:
                    merged.append(v)
                    sub_upgraded = True
                    print("Added to config option %r: %s" % (str(key), str(v)))
                    continue

        return merged, sub_upgraded

    def upgrade_settings(self, currents):
        upgraded_settings, upgraded = self.__inner_upgrade(self.base_config, currents)
        return AttrConfig(upgraded_settings), upgraded

    def merge_settings(self, settings_to_merge):
        upgraded_settings, upgraded = self.__inner_upgrade(settings_to_merge, self.conf, overwrite=True)

        self.conf = upgraded_settings

        if upgraded:
            self.dump_config()

        return AttrConfig(upgraded_settings), upgraded
