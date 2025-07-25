"""
Test Configuration for Traktarr Tests

This module provides fixtures and configuration for testing Traktarr.
"""

import pytest
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    return {
        'core': {
            'debug': False
        },
        'trakt': {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret'
        },
        'sonarr': {
            'url': 'http://localhost:8989',
            'api_key': 'test_sonarr_key',
            'quality': 'HD-1080p',
            'root_folder': '/tv',
            'tag': []
        },
        'radarr': {
            'url': 'http://localhost:7878', 
            'api_key': 'test_radarr_key',
            'quality': 'HD-1080p',
            'root_folder': '/movies',
            'tag': [],
            'minimum_availability': 'released'
        },
        'filters': {
            'shows': {
                'blacklisted_genres': [],
                'blacklisted_networks': [],
                'allowed_countries': [],
                'allowed_languages': [],
                'blacklisted_min_runtime': 15,
                'blacklisted_max_runtime': 300,
                'blacklisted_min_year': 1990,
                'blacklisted_max_year': 2030,
                'blacklisted_title_keywords': [],
                'blacklisted_tvdb_ids': [],
                'blacklisted_tmdb_ids': [],
                'blacklisted_imdb_ids': []
            },
            'movies': {
                'blacklisted_genres': [],
                'blacklisted_min_runtime': 60,
                'blacklisted_max_runtime': 300,
                'blacklisted_min_year': 1990,
                'blacklisted_max_year': 2030,
                'blacklisted_title_keywords': [],
                'blacklisted_tmdb_ids': [],
                'blacklisted_imdb_ids': [],
                'rotten_tomatoes': 0
            }
        },
        'automatic': {
            'movies': {
                'anticipated': 3,
                'trending': 2,
                'popular': 3,
                'interval': 6
            },
            'shows': {
                'anticipated': 10,
                'trending': 2,
                'popular': 1,
                'interval': 48
            }
        },
        'notifications': {
            'verbose': True
        }
    }


@pytest.fixture 
def mock_config_file(mock_config, tmp_path):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(mock_config, indent=2))
    return str(config_file)


@pytest.fixture
def mock_cache_file(tmp_path):
    """Create a temporary cache file for testing."""
    cache_file = tmp_path / "cache.db"
    cache_file.touch()
    return str(cache_file)


@pytest.fixture
def mock_log_file(tmp_path):
    """Create a temporary log file for testing."""
    log_file = tmp_path / "activity.log"
    log_file.touch()
    return str(log_file)


@pytest.fixture
def mock_globals():
    """Mock the global variables used throughout Traktarr."""
    with patch('core.business_logic.cfg') as mock_cfg, \
         patch('core.business_logic.log') as mock_log, \
         patch('core.business_logic.notify') as mock_notify:
        
        # Setup mock config object
        mock_cfg.core.debug = False
        mock_cfg.trakt.client_id = 'test_client_id'
        mock_cfg.trakt.client_secret = 'test_client_secret'
        mock_cfg.sonarr.url = 'http://localhost:8989'
        mock_cfg.sonarr.api_key = 'test_sonarr_key'
        mock_cfg.radarr.url = 'http://localhost:7878'
        mock_cfg.radarr.api_key = 'test_radarr_key'
        mock_cfg.filters.shows.blacklisted_genres = []
        mock_cfg.filters.movies.blacklisted_genres = []
        mock_cfg.automatic.movies.anticipated = 3
        mock_cfg.automatic.shows.anticipated = 10
        
        # Setup mock logger
        mock_log.info = Mock()
        mock_log.error = Mock()
        mock_log.warning = Mock()
        mock_log.debug = Mock()
        
        # Setup mock notify
        mock_notify.send = Mock()
        
        yield {
            'cfg': mock_cfg,
            'log': mock_log, 
            'notify': mock_notify
        }


@pytest.fixture
def mock_trakt():
    """Mock Trakt API functionality."""
    with patch('helpers.trakt.Trakt') as mock_trakt_class:
        mock_trakt_instance = Mock()
        mock_trakt_class.return_value = mock_trakt_instance
        
        # Mock common Trakt methods
        mock_trakt_instance.authenticate.return_value = True
        mock_trakt_instance.get_trending_shows.return_value = [
            {'title': 'Test Show', 'ids': {'trakt': 123, 'tvdb': 456}}
        ]
        mock_trakt_instance.get_trending_movies.return_value = [
            {'title': 'Test Movie', 'ids': {'trakt': 789, 'tmdb': 101112}}
        ]
        
        yield mock_trakt_instance


@pytest.fixture
def mock_sonarr():
    """Mock Sonarr API functionality."""
    with patch('helpers.sonarr.Sonarr') as mock_sonarr_class:
        mock_sonarr_instance = Mock()
        mock_sonarr_class.return_value = mock_sonarr_instance
        
        # Mock common Sonarr methods
        mock_sonarr_instance.add_series.return_value = True
        mock_sonarr_instance.get_series.return_value = []
        mock_sonarr_instance.get_root_folders.return_value = [
            {'path': '/tv', 'id': 1}
        ]
        
        yield mock_sonarr_instance


@pytest.fixture
def mock_radarr():
    """Mock Radarr API functionality.""" 
    with patch('helpers.radarr.Radarr') as mock_radarr_class:
        mock_radarr_instance = Mock()
        mock_radarr_class.return_value = mock_radarr_instance
        
        # Mock common Radarr methods
        mock_radarr_instance.add_movie.return_value = True
        mock_radarr_instance.get_movies.return_value = []
        mock_radarr_instance.get_root_folders.return_value = [
            {'path': '/movies', 'id': 1}
        ]
        
        yield mock_radarr_instance


@pytest.fixture
def mock_all_dependencies(mock_globals, mock_trakt, mock_sonarr, mock_radarr):
    """Mock all major dependencies for comprehensive testing."""
    return {
        'globals': mock_globals,
        'trakt': mock_trakt,
        'sonarr': mock_sonarr,
        'radarr': mock_radarr
    }
