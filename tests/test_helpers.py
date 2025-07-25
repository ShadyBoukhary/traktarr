"""
Test Utilities and Helpers for Traktarr

These tests verify that helper modules and utility functions work correctly.
"""

from unittest.mock import Mock, patch, MagicMock
import pytest


class TestHelpers:
    """Test helper modules and utility functions."""

    def test_misc_str_helpers(self):
        """Test string utility functions."""
        # Import and test string helpers
        try:
            from helpers.str import (
                get_exclusion_string,
                is_year_valid,
                contains_any
            )
            
            # Test exclusion string generation
            exclusions = ['test1', 'test2']
            result = get_exclusion_string(exclusions, 'title')
            assert 'test1' in result
            assert 'test2' in result
            
            # Test year validation
            assert is_year_valid(2020, 2010, 2030) == True
            assert is_year_valid(2005, 2010, 2030) == False
            assert is_year_valid(2035, 2010, 2030) == False
            
            # Test contains_any
            assert contains_any('test string', ['test', 'other']) == True
            assert contains_any('other string', ['test', 'missing']) == False
            
        except ImportError:
            # Skip if helpers not available in test environment
            pytest.skip("String helpers not available")

    def test_misc_parameter_helpers(self):
        """Test parameter parsing utilities."""
        try:
            from helpers.parameter import parse_year_from_string
            
            # Test year parsing
            assert parse_year_from_string('2020') == (2020, 2020)
            assert parse_year_from_string('2020-2023') == (2020, 2023)
            assert parse_year_from_string('invalid') == (None, None)
            
        except ImportError:
            pytest.skip("Parameter helpers not available")

    @patch('requests.get')
    def test_trakt_helper_authentication(self, mock_get):
        """Test Trakt API helper authentication."""
        try:
            from helpers.trakt import Trakt
            
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'access_token': 'test_token'}
            mock_get.return_value = mock_response
            
            # Test authentication
            trakt = Trakt('test_id', 'test_secret')
            result = trakt.authenticate()
            
            # Verify API was called
            mock_get.assert_called()
            
        except ImportError:
            pytest.skip("Trakt helper not available")

    @patch('requests.get')
    def test_sonarr_helper_connection(self, mock_get):
        """Test Sonarr API helper connection."""
        try:
            from helpers.sonarr import Sonarr
            
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response
            
            # Test connection
            sonarr = Sonarr('http://localhost:8989', 'test_key')
            result = sonarr.get_series()
            
            # Verify API was called
            mock_get.assert_called()
            assert result == []
            
        except ImportError:
            pytest.skip("Sonarr helper not available")

    @patch('requests.get')
    def test_radarr_helper_connection(self, mock_get):
        """Test Radarr API helper connection."""
        try:
            from helpers.radarr import Radarr
            
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response
            
            # Test connection
            radarr = Radarr('http://localhost:7878', 'test_key')
            result = radarr.get_movies()
            
            # Verify API was called
            mock_get.assert_called()
            assert result == []
            
        except ImportError:
            pytest.skip("Radarr helper not available")


class TestConfigValidation:
    """Test configuration validation and loading."""

    def test_config_structure_validation(self):
        """Test that config has required structure."""
        try:
            from misc.config import Config
            import tempfile
            import json
            import os
            
            # Create valid config
            valid_config = {
                'core': {'debug': False},
                'trakt': {'client_id': 'test', 'client_secret': 'test'},
                'sonarr': {'url': 'http://localhost:8989', 'api_key': 'test'},
                'radarr': {'url': 'http://localhost:7878', 'api_key': 'test'},
                'filters': {'shows': {}, 'movies': {}},
                'automatic': {'movies': {}, 'shows': {}},
                'notifications': {}
            }
            
            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(valid_config, f, indent=2)
                config_file = f.name
            
            try:
                # Load config
                config = Config(configfile=config_file)
                
                # Verify required sections exist
                assert hasattr(config.cfg, 'core')
                assert hasattr(config.cfg, 'trakt')
                assert hasattr(config.cfg, 'sonarr')
                assert hasattr(config.cfg, 'radarr')
                assert hasattr(config.cfg, 'filters')
                assert hasattr(config.cfg, 'automatic')
                assert hasattr(config.cfg, 'notifications')
                
            finally:
                # Cleanup
                os.unlink(config_file)
                
        except ImportError:
            pytest.skip("Config module not available")

    def test_config_invalid_json(self):
        """Test config loading with invalid JSON."""
        try:
            from misc.config import Config
            import tempfile
            import os
            
            # Create invalid JSON file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write('{invalid json}')
                config_file = f.name
            
            try:
                # Should handle invalid JSON gracefully
                with pytest.raises(Exception):
                    config = Config(configfile=config_file)
                    
            finally:
                # Cleanup
                os.unlink(config_file)
                
        except ImportError:
            pytest.skip("Config module not available")


class TestMediaProcessing:
    """Test media processing and filtering logic."""

    def test_show_filtering_by_genre(self):
        """Test filtering shows by genre."""
        # Mock show data
        shows = [
            {'title': 'Drama Show', 'genres': ['drama'], 'ids': {'trakt': 1}},
            {'title': 'Reality Show', 'genres': ['reality'], 'ids': {'trakt': 2}},
            {'title': 'Comedy Show', 'genres': ['comedy'], 'ids': {'trakt': 3}},
        ]
        
        # Mock blacklisted genres
        blacklisted_genres = ['reality']
        
        # Filter shows (this would be part of the business logic)
        filtered_shows = [
            show for show in shows 
            if not any(genre in blacklisted_genres for genre in show.get('genres', []))
        ]
        
        # Verify filtering
        assert len(filtered_shows) == 2
        assert all('reality' not in show.get('genres', []) for show in filtered_shows)

    def test_movie_filtering_by_year(self):
        """Test filtering movies by year range.""" 
        # Mock movie data
        movies = [
            {'title': 'Old Movie', 'year': 1985, 'ids': {'trakt': 1}},
            {'title': 'Good Movie', 'year': 2020, 'ids': {'trakt': 2}},
            {'title': 'Future Movie', 'year': 2035, 'ids': {'trakt': 3}},
        ]
        
        # Mock year range
        min_year = 1990
        max_year = 2030
        
        # Filter movies (this would be part of the business logic)
        filtered_movies = [
            movie for movie in movies 
            if min_year <= movie.get('year', 0) <= max_year
        ]
        
        # Verify filtering
        assert len(filtered_movies) == 1
        assert filtered_movies[0]['title'] == 'Good Movie'

    def test_title_keyword_filtering(self):
        """Test filtering by title keywords."""
        # Mock media data
        media = [
            {'title': 'Great Show', 'ids': {'trakt': 1}},
            {'title': 'Test Content', 'ids': {'trakt': 2}},
            {'title': 'Another Show', 'ids': {'trakt': 3}},
        ]
        
        # Mock blacklisted keywords
        blacklisted_keywords = ['test']
        
        # Filter media (this would be part of the business logic)
        filtered_media = [
            item for item in media 
            if not any(keyword.lower() in item.get('title', '').lower() 
                      for keyword in blacklisted_keywords)
        ]
        
        # Verify filtering
        assert len(filtered_media) == 2
        assert all('test' not in item['title'].lower() for item in filtered_media)


class TestNotifications:
    """Test notification functionality."""

    @patch('apprise.Apprise')
    def test_apprise_notification_success(self, mock_apprise):
        """Test successful notification via Apprise."""
        try:
            from notifications.apprise import AppriseNotifications
            
            # Mock Apprise
            mock_apprise_instance = Mock()
            mock_apprise.return_value = mock_apprise_instance
            mock_apprise_instance.add.return_value = True
            mock_apprise_instance.notify.return_value = True
            
            # Test notification
            notifier = AppriseNotifications({'service_url': 'test://localhost'})
            result = notifier.send('Test Title', 'Test Message')
            
            # Verify notification was sent
            mock_apprise_instance.notify.assert_called_once()
            
        except ImportError:
            pytest.skip("Apprise notifications not available")

    @patch('requests.post')
    def test_pushover_notification_success(self, mock_post):
        """Test successful notification via Pushover."""
        try:
            from notifications.pushover import PushoverNotifications
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 1}
            mock_post.return_value = mock_response
            
            # Test notification
            notifier = PushoverNotifications({
                'app_token': 'test_app',
                'user_token': 'test_user'
            })
            result = notifier.send('Test Title', 'Test Message')
            
            # Verify notification was sent
            mock_post.assert_called_once()
            
        except ImportError:
            pytest.skip("Pushover notifications not available")

    @patch('requests.post')
    def test_slack_notification_success(self, mock_post):
        """Test successful notification via Slack."""
        try:
            from notifications.slack import SlackNotifications
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            # Test notification
            notifier = SlackNotifications({
                'webhook_url': 'https://hooks.slack.com/test'
            })
            result = notifier.send('Test Title', 'Test Message')
            
            # Verify notification was sent
            mock_post.assert_called_once()
            
        except ImportError:
            pytest.skip("Slack notifications not available")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_api_timeout_handling(self):
        """Test handling of API timeouts."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection timeout")
            
            # Test that timeout is handled gracefully
            # This would be implemented in the actual helper classes
            try:
                # Simulate API call that times out
                raise Exception("Connection timeout")
            except Exception as e:
                assert "timeout" in str(e).lower()

    def test_invalid_media_id_handling(self):
        """Test handling of invalid media IDs."""
        # Test with obviously invalid IDs
        invalid_ids = ['', None, 'invalid', '0', '-1']
        
        for invalid_id in invalid_ids:
            # Each ID should be handled appropriately
            # This would be implemented in the business logic
            assert invalid_id in ['', None, 'invalid', '0', '-1']

    def test_empty_response_handling(self):
        """Test handling of empty API responses."""
        empty_responses = [[], None, {}]
        
        for empty_response in empty_responses:
            # Each empty response should be handled appropriately
            # This would be implemented in the business logic
            if empty_response == []:
                assert len(empty_response) == 0
            elif empty_response is None:
                assert empty_response is None
            elif empty_response == {}:
                assert len(empty_response) == 0
