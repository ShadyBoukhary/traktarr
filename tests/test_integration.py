"""
Integration Tests for Traktarr

These tests verify that the CLI and business logic work together correctly
with realistic configurations and data flows.
"""

from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os
from click.testing import CliRunner

from cli.commands import app


class TestIntegration:
    """Integration tests for end-to-end functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.runner = CliRunner()
        
        # Create a realistic mock config
        self.mock_config = {
            'core': {'debug': False},
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
                    'blacklisted_genres': ['reality'],
                    'blacklisted_networks': [],
                    'allowed_countries': ['us'],
                    'allowed_languages': ['en'],
                    'blacklisted_min_runtime': 15,
                    'blacklisted_max_runtime': 300,
                    'blacklisted_min_year': 1990,
                    'blacklisted_max_year': 2030,
                    'blacklisted_title_keywords': ['test'],
                    'blacklisted_tvdb_ids': [],
                    'blacklisted_tmdb_ids': [],
                    'blacklisted_imdb_ids': []
                },
                'movies': {
                    'blacklisted_genres': ['documentary'],
                    'blacklisted_min_runtime': 60,
                    'blacklisted_max_runtime': 300,
                    'blacklisted_min_year': 1990,
                    'blacklisted_max_year': 2030,
                    'blacklisted_title_keywords': ['test'],
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
            'notifications': {'verbose': True}
        }

    def create_temp_config(self):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.mock_config, f, indent=2)
            return f.name

    @patch('misc.config.Config')
    @patch('misc.log.logger')
    @patch('notifications.Notifications')
    @patch('media.trakt.Trakt')
    def test_end_to_end_trakt_authentication(self, mock_trakt_class, mock_notifications,
                                           mock_logger, mock_config):
        """Test end-to-end Trakt authentication flow."""
        # Setup mocks
        config_file = self.create_temp_config()
        
        # Mock config loading
        mock_config_instance = Mock()
        mock_config.return_value.cfg = mock_config_instance
        mock_config_instance.filters.movies.blacklist_title_keywords = None
        mock_config_instance.filters.movies.rating_limit = None
        mock_config_instance.radarr.profile = None
        mock_config_instance.sonarr.profile = None
        
        # Mock logger
        mock_logger_instance = Mock()
        mock_logger.get_logger.return_value = mock_logger_instance
        
        # Mock notifications
        mock_notifications_instance = Mock()
        mock_notifications.return_value = mock_notifications_instance
        
        # Mock Trakt API
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        mock_trakt.authenticate.return_value = True
        
        try:
            # Run the CLI command
            result = self.runner.invoke(app, [
                '--config', config_file,
                'trakt-auth'
            ])
            
            # Verify success
            assert result.exit_code == 0
            mock_trakt.authenticate.assert_called_once()
            
        finally:
            # Cleanup
            os.unlink(config_file)

    @patch('misc.config.Config')
    @patch('misc.log.logger')
    @patch('notifications.Notifications')
    @patch('media.trakt.Trakt')
    @patch('media.sonarr.Sonarr')
    def test_end_to_end_add_single_show(self, mock_sonarr_class, mock_trakt_class,
                                       mock_notifications, mock_logger, mock_config):
        """Test end-to-end adding a single show."""
        # Setup mocks
        config_file = self.create_temp_config()
        
        # Mock config loading
        mock_config_instance = Mock()
        mock_config.return_value.cfg = mock_config_instance
        mock_config_instance.filters.movies.blacklist_title_keywords = None
        mock_config_instance.filters.movies.rating_limit = None
        mock_config_instance.radarr.profile = None
        mock_config_instance.sonarr.profile = None
        mock_config_instance.sonarr.url = 'http://localhost:8989'
        mock_config_instance.sonarr.api_key = 'test_key'
        
        # Mock logger
        mock_logger_instance = Mock()
        mock_logger.get_logger.return_value = mock_logger_instance
        
        # Mock notifications
        mock_notifications_instance = Mock()
        mock_notifications.return_value = mock_notifications_instance
        
        # Mock Trakt API
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        mock_trakt.get_show.return_value = {
            'title': 'Breaking Bad',
            'year': 2008,
            'ids': {'trakt': 1388, 'tvdb': 81189}
        }
        
        # Mock Media Trakt
        mock_media_trakt_instance = Mock()
        mock_media_trakt.return_value = mock_media_trakt_instance
        mock_media_trakt_instance.shows_to_tvdb_dict.return_value = {1388: 81189}
        
        # Mock Sonarr API
        mock_sonarr = Mock()
        mock_sonarr_class.return_value = mock_sonarr
        mock_sonarr.add_series.return_value = True
        
        try:
            # Run the CLI command
            result = self.runner.invoke(app, [
                '--config', config_file,
                'show',
                '--show-id', '1388'
            ])
            
            # Verify success
            assert result.exit_code == 0
            mock_trakt.get_show.assert_called()
            mock_sonarr.add_series.assert_called()
            
        finally:
            # Cleanup
            os.unlink(config_file)

    @patch('misc.config.Config')
    @patch('misc.log.logger') 
    @patch('notifications.Notifications')
    @patch('helpers.trakt.Trakt')
    @patch('helpers.radarr.Radarr')
    @patch('media.trakt.Trakt')
    def test_end_to_end_add_single_movie(self, mock_media_trakt, mock_radarr_class,
                                        mock_trakt_class, mock_notifications,
                                        mock_logger, mock_config):
        """Test end-to-end adding a single movie."""
        # Setup mocks
        config_file = self.create_temp_config()
        
        # Mock config loading
        mock_config_instance = Mock()
        mock_config.return_value.cfg = mock_config_instance
        mock_config_instance.filters.movies.blacklist_title_keywords = None
        mock_config_instance.filters.movies.rating_limit = None
        mock_config_instance.radarr.profile = None
        mock_config_instance.sonarr.profile = None
        mock_config_instance.radarr.url = 'http://localhost:7878'
        mock_config_instance.radarr.api_key = 'test_key'
        
        # Mock logger
        mock_logger_instance = Mock()
        mock_logger.get_logger.return_value = mock_logger_instance
        
        # Mock notifications
        mock_notifications_instance = Mock()
        mock_notifications.return_value = mock_notifications_instance
        
        # Mock Trakt API
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        mock_trakt.get_movie.return_value = {
            'title': 'The Shawshank Redemption',
            'year': 1994,
            'ids': {'trakt': 1, 'tmdb': 278}
        }
        
        # Mock Media Trakt
        mock_media_trakt_instance = Mock()
        mock_media_trakt.return_value = mock_media_trakt_instance
        mock_media_trakt_instance.movies_to_tmdb_dict.return_value = {1: 278}
        
        # Mock Radarr API
        mock_radarr = Mock()
        mock_radarr_class.return_value = mock_radarr
        mock_radarr.add_movie.return_value = True
        
        try:
            # Run the CLI command
            result = self.runner.invoke(app, [
                '--config', config_file,
                'movie',
                '--movie-id', '1'
            ])
            
            # Verify success
            assert result.exit_code == 0
            mock_trakt.get_movie.assert_called()
            mock_radarr.add_movie.assert_called()
            
        finally:
            # Cleanup
            os.unlink(config_file)

    @patch('misc.config.Config')
    @patch('misc.log.logger')
    @patch('notifications.Notifications')
    @patch('helpers.trakt.Trakt')
    @patch('helpers.sonarr.Sonarr')
    @patch('media.trakt.Trakt')
    def test_end_to_end_add_multiple_shows_with_filters(self, mock_media_trakt, mock_sonarr_class,
                                                       mock_trakt_class, mock_notifications,
                                                       mock_logger, mock_config):
        """Test end-to-end adding multiple shows with filtering."""
        # Setup mocks
        config_file = self.create_temp_config()
        
        # Mock config loading
        mock_config_instance = Mock()
        mock_config.return_value.cfg = mock_config_instance
        mock_config_instance.filters.movies.blacklist_title_keywords = None
        mock_config_instance.filters.movies.rating_limit = None
        mock_config_instance.radarr.profile = None
        mock_config_instance.sonarr.profile = None
        mock_config_instance.sonarr.url = 'http://localhost:8989'
        mock_config_instance.sonarr.api_key = 'test_key'
        mock_config_instance.filters.shows.blacklisted_genres = ['reality']
        mock_config_instance.filters.shows.blacklisted_title_keywords = ['test']
        
        # Mock logger
        mock_logger_instance = Mock()
        mock_logger.get_logger.return_value = mock_logger_instance
        
        # Mock notifications
        mock_notifications_instance = Mock()
        mock_notifications.return_value = mock_notifications_instance
        
        # Mock Trakt API - return mix of valid and filtered shows
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        mock_trakt.get_trending_shows.return_value = [
            {
                'title': 'Good Show',
                'year': 2020,
                'genres': ['drama'],
                'ids': {'trakt': 1, 'tvdb': 101}
            },
            {
                'title': 'Test Reality Show',  # Should be filtered out
                'year': 2021,
                'genres': ['reality'],
                'ids': {'trakt': 2, 'tvdb': 102}
            },
            {
                'title': 'Another Good Show',
                'year': 2019,
                'genres': ['comedy'],
                'ids': {'trakt': 3, 'tvdb': 103}
            }
        ]
        
        # Mock Media Trakt
        mock_media_trakt_instance = Mock()
        mock_media_trakt.return_value = mock_media_trakt_instance
        mock_media_trakt_instance.shows_to_tvdb_dict.return_value = {1: 101, 2: 102, 3: 103}
        
        # Mock Sonarr API
        mock_sonarr = Mock()
        mock_sonarr_class.return_value = mock_sonarr
        mock_sonarr.add_series.return_value = True
        
        try:
            # Run the CLI command
            result = self.runner.invoke(app, [
                '--config', config_file,
                'shows',
                '--list-type', 'trending',
                '--add-limit', '2',
                '--genres', 'drama,comedy'
            ])
            
            # Verify success
            assert result.exit_code == 0
            mock_trakt.get_trending_shows.assert_called()
            
        finally:
            # Cleanup
            os.unlink(config_file)

    @patch('misc.config.Config')
    @patch('misc.log.logger')
    @patch('notifications.Notifications')
    @patch('helpers.trakt.Trakt')
    @patch('helpers.radarr.Radarr')
    @patch('media.trakt.Trakt')
    def test_end_to_end_dry_run_movies(self, mock_media_trakt, mock_radarr_class,
                                      mock_trakt_class, mock_notifications,
                                      mock_logger, mock_config):
        """Test end-to-end dry run for movies."""
        # Setup mocks
        config_file = self.create_temp_config()
        
        # Mock config loading
        mock_config_instance = Mock()
        mock_config.return_value.cfg = mock_config_instance
        mock_config_instance.filters.movies.blacklist_title_keywords = None
        mock_config_instance.filters.movies.rating_limit = None
        mock_config_instance.radarr.profile = None
        mock_config_instance.sonarr.profile = None
        mock_config_instance.radarr.url = 'http://localhost:7878'
        mock_config_instance.radarr.api_key = 'test_key'
        mock_config_instance.filters.movies.blacklisted_genres = ['documentary']
        
        # Mock logger
        mock_logger_instance = Mock()
        mock_logger.get_logger.return_value = mock_logger_instance
        
        # Mock notifications
        mock_notifications_instance = Mock()
        mock_notifications.return_value = mock_notifications_instance
        
        # Mock Trakt API
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        mock_trakt.get_popular_movies.return_value = [
            {
                'title': 'Popular Movie 1',
                'year': 2023,
                'genres': ['action'],
                'ids': {'trakt': 1, 'tmdb': 201}
            },
            {
                'title': 'Popular Movie 2',
                'year': 2022,
                'genres': ['thriller'],
                'ids': {'trakt': 2, 'tmdb': 202}
            }
        ]
        
        # Mock Media Trakt
        mock_media_trakt_instance = Mock()
        mock_media_trakt.return_value = mock_media_trakt_instance
        mock_media_trakt_instance.movies_to_tmdb_dict.return_value = {1: 201, 2: 202}
        
        # Mock Radarr API
        mock_radarr = Mock()
        mock_radarr_class.return_value = mock_radarr
        
        try:
            # Run the CLI command in dry run mode
            result = self.runner.invoke(app, [
                '--config', config_file,
                'movies',
                '--list-type', 'popular',
                '--dry-run'
            ])
            
            # Verify success and no actual additions
            assert result.exit_code == 0
            mock_trakt.get_popular_movies.assert_called()
            mock_radarr.add_movie.assert_not_called()  # Should not add in dry run
            
        finally:
            # Cleanup
            os.unlink(config_file)

    @patch('misc.config.Config')
    @patch('misc.log.logger')
    @patch('notifications.Notifications')
    def test_config_validation_missing_file(self, mock_notifications, mock_logger, mock_config):
        """Test behavior with missing config file."""
        # Mock config to raise an exception
        mock_config.side_effect = FileNotFoundError("Config file not found")
        
        # Run the CLI command with non-existent config
        result = self.runner.invoke(app, [
            '--config', '/nonexistent/config.json',
            'trakt-auth'
        ])
        
        # Should handle the error gracefully
        assert result.exit_code != 0

    @patch('misc.config.Config')
    @patch('misc.log.logger')
    @patch('notifications.Notifications')
    @patch('helpers.trakt.Trakt')
    def test_api_connection_failure(self, mock_trakt_class, mock_notifications,
                                   mock_logger, mock_config):
        """Test behavior when API connections fail."""
        # Setup mocks
        config_file = self.create_temp_config()
        
        # Mock config loading
        mock_config_instance = Mock()
        mock_config.return_value.cfg = mock_config_instance
        mock_config_instance.filters.movies.blacklist_title_keywords = None
        mock_config_instance.filters.movies.rating_limit = None
        mock_config_instance.radarr.profile = None
        mock_config_instance.sonarr.profile = None
        
        # Mock logger
        mock_logger_instance = Mock()
        mock_logger.get_logger.return_value = mock_logger_instance
        
        # Mock notifications
        mock_notifications_instance = Mock()
        mock_notifications.return_value = mock_notifications_instance
        
        # Mock Trakt API to fail
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        mock_trakt.authenticate.side_effect = Exception("API connection failed")
        
        try:
            # Run the CLI command
            result = self.runner.invoke(app, [
                '--config', config_file,
                'trakt-auth'
            ])
            
            # Should handle the error gracefully
            # Exact behavior depends on error handling implementation
            mock_logger_instance.error.assert_called()
            
        finally:
            # Cleanup
            os.unlink(config_file)
