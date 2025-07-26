"""Tests for automatic mode functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from misc.config import Config, Singleton
from core.business_logic import (
    run_automatic_mode,
    _automatic_media,
    automatic_movies_public_lists,
    automatic_movies_user_lists,
    automatic_shows_public_lists,
    automatic_shows_user_lists,
)


@pytest.fixture(autouse=True)
def clear_singleton():
    """Clear singleton instances before and after each test."""
    Singleton._instances = {}
    yield
    Singleton._instances = {}


@pytest.fixture
def mock_schedule_and_time():
    """Mock schedule and time modules in business logic."""
    import core.business_logic
    original_schedule = core.business_logic.schedule
    original_time = core.business_logic.time
    
    # Create mock schedule
    mock_schedule = Mock()
    mock_schedule.every = Mock()
    mock_schedule.run_pending = Mock()
    mock_schedule.idle_seconds = Mock()
    mock_schedule.next_run = Mock()
    
    # Create mock time
    mock_time_module = Mock()
    mock_time_module.time = Mock()
    mock_time_module.sleep = Mock()
    
    # Replace the modules
    core.business_logic.schedule = mock_schedule
    core.business_logic.time = mock_time_module
    
    yield mock_schedule, mock_time_module
    
    # Restore original modules
    core.business_logic.schedule = original_schedule
    core.business_logic.time = original_time


@pytest.fixture
def mock_config():
    """Mock configuration for automatic mode tests."""
    config = Mock()
    
    # Mock automatic configuration
    config.automatic = Mock()
    config.automatic.movies = Mock()
    config.automatic.shows = Mock()
    
    # Mock intervals configuration
    config.automatic.movies.intervals = {
        'public_lists': 24,
        'user_lists': 12
    }
    config.automatic.shows.intervals = {
        'public_lists': 48,
        'user_lists': 6
    }
    
    # Mock individual list configurations for _automatic_media
    # This is what gets used in automatic_config.items()
    config.automatic.movies.items = Mock(return_value=[
        ('anticipated', 3),
        ('popular', 5),
        ('trending', 2),
        ('boxoffice', 10),
        ('watchlist', {'testuser': 5}),
        ('lists', {'custom-list': 3})
    ])
    
    config.automatic.shows.items = Mock(return_value=[
        ('anticipated', 10),
        ('popular', 1),
        ('trending', 2),
        ('watched_monthly', 2),
        ('played', 2),
        ('watchlist', {'testuser': 3}),
        ('lists', {'custom-show-list': 2})
    ])
    
    # Mock filters
    config.filters = Mock()
    config.filters.movies = Mock()
    config.filters.movies.rotten_tomatoes = "70"
    config.filters.movies.disabled_for = []
    config.filters.shows = Mock()
    config.filters.shows.disabled_for = []
    
    # Mock notifications
    config.notifications = Mock()
    config.notifications.verbose = True
    
    # Mock API configurations
    config.radarr = {'test_instance': {'api_url': 'http://radarr:7878', 'api_key': 'test_key'}}
    config.sonarr = {'test_instance': {'api_url': 'http://sonarr:8989', 'api_key': 'test_key'}}
    config.trakt = {'api_key': 'test_key'}
    
    return config


class TestAutomaticMedia:
    """Test the _automatic_media function."""
    
    @patch('core.business_logic.log')
    @patch('core.business_logic.notify')
    @patch('media.trakt.Trakt')
    @patch('time.sleep')
    def test_automatic_movies_public_lists(self, mock_sleep, mock_trakt_class, mock_notify, mock_log, mock_config):
        """Test automatic media processing for movies public lists."""
        # Set the mock cfg as a module-level variable
        import core.business_logic
        core.business_logic.cfg = mock_config
        
        # Mock Trakt instance and methods
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        
        # Define non_user_lists attribute
        mock_trakt_class.non_user_lists = ['anticipated', 'popular', 'trending', 'boxoffice']
        
        # Mock get list methods
        mock_trakt.get_anticipated_movies.return_value = [
            {'title': 'Movie 1', 'year': 2024, 'ids': {'imdb': 'tt1234567', 'tmdb': 12345, 'trakt': 54321}},
            {'title': 'Movie 2', 'year': 2024, 'ids': {'imdb': 'tt2345678', 'tmdb': 23456, 'trakt': 65432}}
        ]
        mock_trakt.get_popular_movies.return_value = [
            {'title': 'Popular Movie', 'year': 2024, 'ids': {'imdb': 'tt3456789', 'tmdb': 34567, 'trakt': 76543}}
        ]
        mock_trakt.get_trending_movies.return_value = []
        mock_trakt.get_boxoffice_movies.return_value = []
        mock_trakt.get_watchlist_movies.return_value = []
        mock_trakt.get_user_list_movies.return_value = []
        
        # Mock _process_media to avoid actual API calls
        with patch('core.business_logic._process_media') as mock_process:
            mock_process.return_value = 2  # Return number of items added
            
            result = _automatic_media(
                media_type='movies',
                list_filter='public_lists',
                add_delay=1.0,
                sort='votes',
                no_search=False,
                notifications=True,
                ignore_blacklist=False,
                rotten_tomatoes=70
            )
        
        # Verify the result
        assert result > 0
        
        # Verify _process_media was called for public lists only
        assert mock_process.call_count == 4  # 4 public lists
        
        # Verify each call had the expected parameters
        public_lists = ['anticipated', 'popular', 'trending', 'boxoffice']
        called_lists = [call[1]['list_type'] for call in mock_process.call_args_list]
        for list_type in public_lists:
            assert list_type in called_lists
        
        # Verify sleep was called between adds
        assert mock_sleep.call_count > 0
    
    @patch('core.business_logic.log')
    @patch('core.business_logic.notify')
    @patch('media.trakt.Trakt')
    @patch('time.sleep')
    def test_automatic_shows_user_lists(self, mock_sleep, mock_trakt_class, mock_notify, mock_log, mock_config):
        """Test automatic media processing for shows user lists."""
        # Set the mock cfg as a module-level variable
        import core.business_logic
        core.business_logic.cfg = mock_config
        
        # Mock Trakt instance and methods
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        
        # Define non_user_lists attribute
        mock_trakt_class.non_user_lists = ['anticipated', 'popular', 'trending', 'watched_monthly', 'played']
        
        # Mock user list methods - only return data for user lists
        mock_trakt.get_anticipated_shows.return_value = []
        mock_trakt.get_popular_shows.return_value = []
        mock_trakt.get_trending_shows.return_value = []
        mock_trakt.get_most_watched_shows.return_value = []
        mock_trakt.get_most_played_shows.return_value = []
        
        # Mock watchlist and custom lists
        mock_trakt.get_watchlist_shows.return_value = [
            {'title': 'Watchlist Show', 'year': 2024, 'ids': {'imdb': 'tt1111111', 'tmdb': 11111, 'trakt': 11111}}
        ]
        mock_trakt.get_user_list_shows.return_value = [
            {'title': 'Custom List Show', 'year': 2024, 'ids': {'imdb': 'tt2222222', 'tmdb': 22222, 'trakt': 22222}}
        ]
        
        # Mock _process_media to avoid actual API calls
        with patch('core.business_logic._process_media') as mock_process:
            mock_process.return_value = 1  # Return number of items added
            
            result = _automatic_media(
                media_type='shows',
                list_filter='user_lists',
                add_delay=0.5,
                sort='rating',
                no_search=True,
                notifications=False,
                ignore_blacklist=True
            )
        
        # Verify the result
        assert result > 0
        
        # Verify _process_media was called for user lists only (watchlist + custom lists)
        assert mock_process.call_count == 2  # watchlist + custom lists
        
        # Verify user list types were processed
        called_lists = [call[1]['list_type'] for call in mock_process.call_args_list]
        assert 'watchlist' in called_lists
        assert 'custom-show-list' in called_lists
    
    @patch('core.business_logic.log')
    @patch('core.business_logic.notify')
    def test_automatic_media_invalid_type(self, mock_notify, mock_log, mock_config):
        """Test automatic media with invalid media type."""
        # Set the mock cfg as a module-level variable
        import core.business_logic
        core.business_logic.cfg = mock_config
        
        with pytest.raises(ValueError, match="Invalid media_type: invalid"):
            _automatic_media(
                media_type='invalid',
                list_filter='public_lists'
            )
    
    @patch('core.business_logic.log')
    @patch('core.business_logic.notify')
    @patch('media.trakt.Trakt')
    @patch('time.sleep')
    def test_automatic_media_no_lists_filter(self, mock_sleep, mock_trakt_class, mock_notify, mock_log, mock_config):
        """Test automatic media processing with no list filter (processes all)."""
        # Set the mock cfg as a module-level variable
        import core.business_logic
        core.business_logic.cfg = mock_config
        
        # Mock Trakt instance and methods
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        
        # Define non_user_lists attribute
        mock_trakt_class.non_user_lists = ['anticipated', 'popular', 'trending', 'boxoffice']
        
        # Mock all list methods to return empty lists for simplicity
        for method_name in ['get_anticipated_movies', 'get_popular_movies', 'get_trending_movies', 
                           'get_boxoffice_movies', 'get_watchlist_movies', 'get_user_list_movies']:
            getattr(mock_trakt, method_name).return_value = []
        
        # Mock _process_media to return 0 since no media found
        with patch('core.business_logic._process_media') as mock_process:
            mock_process.return_value = 0
            
            result = _automatic_media(
                media_type='movies',
                list_filter=None,  # No filter - should process all lists
                add_delay=0.1
            )
        
        # Should process but add 0 items since all lists are empty
        assert result == 0
        
        # Should have processed all lists (public + user)
        assert mock_process.call_count == 6  # All 6 movie list types


class TestAutomaticHelperFunctions:
    """Test the automatic helper functions."""
    
    @patch('core.business_logic._automatic_media')
    def test_automatic_movies_public_lists(self, mock_automatic_media):
        """Test automatic_movies_public_lists function."""
        mock_automatic_media.return_value = 5
        
        result = automatic_movies_public_lists(
            add_delay=2.0,
            sort='rating',
            no_search=True,
            notifications=True,
            ignore_blacklist=False,
            rotten_tomatoes=80
        )
        
        assert result == 5
        mock_automatic_media.assert_called_once_with(
            'movies',
            list_filter='public_lists',
            add_delay=2.0,
            sort='rating',
            no_search=True,
            notifications=True,
            ignore_blacklist=False,
            rotten_tomatoes=80
        )
    
    @patch('core.business_logic._automatic_media')
    def test_automatic_shows_user_lists(self, mock_automatic_media):
        """Test automatic_shows_user_lists function."""
        mock_automatic_media.return_value = 3
        
        result = automatic_shows_user_lists(
            add_delay=1.5,
            sort='release',
            no_search=False,
            notifications=False,
            ignore_blacklist=True
        )
        
        assert result == 3
        mock_automatic_media.assert_called_once_with(
            'shows',
            list_filter='user_lists',
            add_delay=1.5,
            sort='release',
            no_search=False,
            notifications=False,
            ignore_blacklist=True
        )


class TestRunAutomaticMode:
    """Test the run_automatic_mode function."""
    
    @patch('core.business_logic.cfg')
    @patch('core.business_logic.notify')
    @patch('core.business_logic.log')
    def test_run_automatic_mode_basic_scheduling(self, mock_log, mock_notify, mock_cfg, mock_schedule_and_time):
        """Test basic scheduling functionality in automatic mode."""
        mock_schedule, mock_time_module = mock_schedule_and_time
        
        # Configure the mocked config
        mock_cfg.automatic = Mock()
        mock_cfg.automatic.movies = Mock()
        mock_cfg.automatic.shows = Mock()
        mock_cfg.automatic.movies.intervals = {'public_lists': 24, 'user_lists': 12}
        mock_cfg.automatic.shows.intervals = {'public_lists': 8, 'user_lists': 6}
        
        # Configure other required config
        mock_cfg.notifications = Mock()
        mock_cfg.notifications.verbose = True
        mock_cfg.filters = Mock()
        mock_cfg.filters.movies = Mock()
        mock_cfg.filters.movies.rotten_tomatoes = ""
        
        # Mock schedule library
        mock_task = Mock()
        mock_task.tag = 'test_task'
        mock_task.next_run = Mock()
        mock_task.next_run.strftime.return_value = '2024-01-01 12:00:00'
        mock_task.run.return_value = None

        mock_every_hours = Mock()
        mock_every_hours.do.return_value = mock_task
        mock_schedule.every.return_value = Mock()
        mock_schedule.every.return_value.hours = mock_every_hours

        mock_schedule.idle_seconds.side_effect = [3600, 0, -1]  # First sleep, then run, then exit
        mock_schedule.next_run.return_value = Mock()
        mock_schedule.next_run.return_value.strftime.return_value = '2024-01-01 13:00:00'
        
        # Mock time progression
        mock_time_module.time.side_effect = [0, 1, 2, 3600, 3601]  # Time progression for log intervals

        # Mock the automatic functions to avoid calling them
        with patch('core.business_logic.automatic_movies_public_lists') as mock_movies_pub, \
             patch('core.business_logic.automatic_movies_user_lists') as mock_movies_user, \
             patch('core.business_logic.automatic_shows_public_lists') as mock_shows_pub, \
             patch('core.business_logic.automatic_shows_user_lists') as mock_shows_user:

            mock_movies_pub.return_value = 2
            mock_movies_user.return_value = 1
            mock_shows_pub.return_value = 3
            mock_shows_user.return_value = 1

            # Run for limited iterations to avoid infinite loop
            iteration_count = 0
            def side_effect_run_pending():
                nonlocal iteration_count
                iteration_count += 1
                if iteration_count >= 3:  # Stop after 3 iterations
                    raise KeyboardInterrupt("Test termination")

            mock_schedule.run_pending.side_effect = side_effect_run_pending

            # Test should exit via KeyboardInterrupt
            with pytest.raises(KeyboardInterrupt):
                from core.business_logic import run_automatic_mode
                run_automatic_mode(
                    add_delay=1.0,
                    sort='votes',
                    no_search=False,
                    run_now=False,
                    no_notifications=False,
                    ignore_blacklist=False
                )

        # Verify scheduling was attempted for all 4 task types
        assert mock_schedule.every.call_count == 4
        
        # Verify the main loop functions were called
        assert mock_schedule.run_pending.call_count >= 1
        assert mock_schedule.idle_seconds.call_count >= 1
        assert mock_time_module.sleep.call_count >= 1
        
        # Verify initial logging
        mock_log.info.assert_any_call("Automatic mode is now running.")
        mock_log.info.assert_any_call("Successfully scheduled %d automatic tasks", 4)
    
    @patch('core.business_logic.cfg')
    @patch('core.business_logic.notify')
    @patch('core.business_logic.log')
    def test_run_automatic_mode_with_run_now(self, mock_log, mock_notify, mock_cfg, mock_schedule_and_time):
        """Test automatic mode with run_now option."""
        mock_schedule, mock_time_module = mock_schedule_and_time
        
        # Configure intervals so tasks will be scheduled
        mock_cfg.automatic = Mock()
        mock_cfg.automatic.movies = Mock()
        mock_cfg.automatic.shows = Mock()
        mock_cfg.automatic.movies.intervals = {'public_lists': 24, 'user_lists': 12}
        mock_cfg.automatic.shows.intervals = {'public_lists': 8, 'user_lists': 6}
        
        # Configure other required config
        mock_cfg.notifications = Mock()
        mock_cfg.notifications.verbose = True
        mock_cfg.filters = Mock()
        mock_cfg.filters.movies = Mock()
        mock_cfg.filters.movies.rotten_tomatoes = ""
        
        # Mock time
        mock_time_module.time.return_value = 0
        
        # Mock schedule library
        mock_task = Mock()
        mock_task.tag = 'test_task'
        mock_task.next_run = Mock()
        mock_task.next_run.strftime.return_value = '2024-01-01 12:00:00'
        mock_task.run.return_value = None
        
        mock_every_hours = Mock()
        mock_every_hours.do.return_value = mock_task
        mock_schedule.every.return_value = Mock()
        mock_schedule.every.return_value.hours = mock_every_hours
        
        mock_schedule.idle_seconds.return_value = -1  # Force immediate exit
        
        # Mock the automatic functions
        with patch('core.business_logic.automatic_movies_public_lists') as mock_movies_pub, \
             patch('core.business_logic.automatic_movies_user_lists') as mock_movies_user, \
             patch('core.business_logic.automatic_shows_public_lists') as mock_shows_pub, \
             patch('core.business_logic.automatic_shows_user_lists') as mock_shows_user:
            
            mock_movies_pub.return_value = 2
            mock_movies_user.return_value = 1
            mock_shows_pub.return_value = 3
            mock_shows_user.return_value = 1
            
            # Limit iterations to avoid infinite loop
            iteration_count = 0
            def side_effect_run_pending():
                nonlocal iteration_count
                iteration_count += 1
                if iteration_count >= 2:
                    raise KeyboardInterrupt("Test termination")
            
            mock_schedule.run_pending.side_effect = side_effect_run_pending
            
            with pytest.raises(KeyboardInterrupt):
                from core.business_logic import run_automatic_mode
                run_automatic_mode(
                    add_delay=0.5,
                    sort='rating',
                    no_search=True,
                    run_now=True,  # Should run tasks immediately
                    no_notifications=True,
                    ignore_blacklist=True
                )
        
        # Verify tasks were run immediately (task.run() called)
        assert mock_task.run.call_count == 4  # All 4 tasks should be run immediately
        
        # Verify sleep was called between immediate runs
        sleep_calls = [call for call in mock_time_module.sleep.call_args_list if call[0][0] == 0.5]
        assert len(sleep_calls) == 4  # Sleep after each immediate run
    
    @patch('core.business_logic.cfg')
    @patch('core.business_logic.notify')
    @patch('core.business_logic.log')
    def test_run_automatic_mode_no_intervals_configured(self, mock_log, mock_notify, mock_cfg, mock_schedule_and_time):
        """Test automatic mode when no intervals are configured."""
        mock_schedule, mock_time_module = mock_schedule_and_time
        
        # Configure no intervals
        mock_cfg.automatic = Mock()
        mock_cfg.automatic.movies = Mock()
        mock_cfg.automatic.shows = Mock()
        mock_cfg.automatic.movies.intervals = {}
        mock_cfg.automatic.shows.intervals = {}
        
        # Configure other required config
        mock_cfg.notifications = Mock()
        mock_cfg.notifications.verbose = False  # Disable to avoid notify.send calls
        
        # Mock schedule to avoid actually scheduling
        mock_schedule.every.return_value = Mock()
        
        # Mock time module
        mock_time_module.time.return_value = 0
        
        # Make sure the main loop exits immediately
        # Since no tasks are scheduled, idle_seconds() should return a value that causes immediate sleep
        mock_schedule.idle_seconds.return_value = 1  # Return a small value
        mock_schedule.next_run.return_value = None  # No next run since no tasks
        
        # Mock run_pending to exit immediately after the first call
        mock_schedule.run_pending.side_effect = KeyboardInterrupt("Test termination")
        
        with pytest.raises(KeyboardInterrupt):
            from core.business_logic import run_automatic_mode
            run_automatic_mode()
        
        # Verify warning about no tasks scheduled
        mock_log.warning.assert_called_with("No automatic tasks scheduled! Check your intervals configuration.")
        
        # Verify no tasks were actually scheduled
        assert mock_schedule.every.call_count == 0
    
    @patch('core.business_logic.cfg')
    @patch('core.business_logic.notify')
    @patch('core.business_logic.log')
    def test_run_automatic_mode_exception_handling(self, mock_log, mock_notify, mock_cfg, mock_schedule_and_time):
        """Test exception handling in automatic mode main loop."""
        mock_schedule, mock_time_module = mock_schedule_and_time
        
        # Configure intervals so tasks will be scheduled
        mock_cfg.automatic = Mock()
        mock_cfg.automatic.movies = Mock()
        mock_cfg.automatic.shows = Mock()
        mock_cfg.automatic.movies.intervals = {'public_lists': 24, 'user_lists': 12}
        mock_cfg.automatic.shows.intervals = {'public_lists': 8, 'user_lists': 6}
        
        # Configure other required config
        mock_cfg.notifications = Mock()
        mock_cfg.notifications.verbose = False  # Disable to avoid notify.send calls
        mock_cfg.filters = Mock()
        mock_cfg.filters.movies = Mock()
        mock_cfg.filters.movies.rotten_tomatoes = ""
        
        mock_time_module.time.return_value = 0
        
        # Mock schedule library
        mock_task = Mock()
        mock_task.tag = 'test_task'
        mock_task.next_run = Mock()
        mock_task.next_run.strftime.return_value = '2024-01-01 12:00:00'
        
        mock_every_hours = Mock()
        mock_every_hours.do.return_value = mock_task
        mock_schedule.every.return_value = Mock()
        mock_schedule.every.return_value.hours = mock_every_hours
        
        # Make run_pending throw an exception, then exit
        test_exception = Exception("Test exception")
        mock_schedule.run_pending.side_effect = [test_exception, KeyboardInterrupt("Test termination")]
        mock_schedule.idle_seconds.return_value = 1
        
        with patch('core.business_logic.automatic_movies_public_lists'), \
             patch('core.business_logic.automatic_movies_user_lists'), \
             patch('core.business_logic.automatic_shows_public_lists'), \
             patch('core.business_logic.automatic_shows_user_lists'):
            
            with pytest.raises(KeyboardInterrupt):
                from core.business_logic import run_automatic_mode
                run_automatic_mode()
        
        # Verify exception was logged
        mock_log.exception.assert_called_with(
            "Unhandled exception occurred while processing scheduled tasks: %s", 
            test_exception
        )
        
        # Verify recovery sleep was called
        sleep_calls = [call for call in mock_time_module.sleep.call_args_list if call[0][0] == 1]
        assert len(sleep_calls) >= 1
    
    @patch('core.business_logic.cfg')
    @patch('core.business_logic.notify')
    @patch('core.business_logic.log')
    def test_run_automatic_mode_periodic_status_logging(self, mock_log, mock_notify, mock_cfg, mock_schedule_and_time):
        """Test periodic status logging in automatic mode."""
        mock_schedule, mock_time_module = mock_schedule_and_time
        
        # Configure intervals so tasks will be scheduled
        mock_cfg.automatic = Mock()
        mock_cfg.automatic.movies = Mock()
        mock_cfg.automatic.shows = Mock()
        mock_cfg.automatic.movies.intervals = {'public_lists': 24, 'user_lists': 12}
        mock_cfg.automatic.shows.intervals = {'public_lists': 8, 'user_lists': 6}
        
        # Configure other required config
        mock_cfg.notifications = Mock()
        mock_cfg.notifications.verbose = False  # Disable to avoid notify.send calls
        mock_cfg.filters = Mock()
        mock_cfg.filters.movies = Mock()
        mock_cfg.filters.movies.rotten_tomatoes = ""
        
        # Mock time progression to trigger periodic logging
        mock_time_module.time.side_effect = [0, 3600, 3601, 7200, 7201]  # Cross logging thresholds
        
        # Mock multiple schedule tasks to match expected output
        mock_task1 = Mock()
        mock_task1.tag = 'movies public lists'
        mock_task1.next_run = Mock()
        mock_task1.next_run.strftime.return_value = '2024-01-01 12:00:00'
        
        mock_task2 = Mock()
        mock_task2.tag = 'movies user lists'
        mock_task2.next_run = Mock()
        mock_task2.next_run.strftime.return_value = '2024-01-01 13:00:00'
        
        mock_task3 = Mock()
        mock_task3.tag = 'shows public lists'
        mock_task3.next_run = Mock()
        mock_task3.next_run.strftime.return_value = '2024-01-01 14:00:00'
        
        mock_task4 = Mock()
        mock_task4.tag = 'shows user lists'
        mock_task4.next_run = Mock()
        mock_task4.next_run.strftime.return_value = '2024-01-01 15:00:00'
        
        # Set up the task creation sequence
        tasks = [mock_task1, mock_task2, mock_task3, mock_task4]
        task_index = [0]  # Use list to modify in closure
        
        def create_task(*args):
            if task_index[0] < len(tasks):
                task = tasks[task_index[0]]
                task_index[0] += 1
                return task
            return Mock()
        
        mock_every_hours = Mock()
        mock_every_hours.do.side_effect = create_task
        mock_schedule.every.return_value = Mock()
        mock_schedule.every.return_value.hours = mock_every_hours
        
        mock_schedule.idle_seconds.return_value = 1
        mock_schedule.next_run.return_value = Mock()
        mock_schedule.next_run.return_value.strftime.return_value = '2024-01-01 13:00:00'
        
        # Limit iterations
        iteration_count = 0
        def side_effect_run_pending():
            nonlocal iteration_count
            iteration_count += 1
            if iteration_count >= 3:
                raise KeyboardInterrupt("Test termination")
        
        mock_schedule.run_pending.side_effect = side_effect_run_pending
        
        with patch('core.business_logic.automatic_movies_public_lists'), \
             patch('core.business_logic.automatic_movies_user_lists'), \
             patch('core.business_logic.automatic_shows_public_lists'), \
             patch('core.business_logic.automatic_shows_user_lists'):
            
            with pytest.raises(KeyboardInterrupt):
                from core.business_logic import run_automatic_mode
                run_automatic_mode()
        
        # Verify periodic status logging occurred
        status_log_calls = [call for call in mock_log.info.call_args_list 
                           if 'Current schedule status:' in str(call)]
        assert len(status_log_calls) >= 1
        
        # Verify individual task status was logged (more flexible matching)
        task_status_calls = [call for call in mock_log.info.call_args_list 
                            if 'next run at' in str(call)]
        assert len(task_status_calls) >= 1


class TestAutomaticModeIntegration:
    """Integration tests for automatic mode with mocked external dependencies."""
    
    @patch('core.business_logic.cfg')
    @patch('core.business_logic.notify')
    @patch('core.business_logic.log')
    @patch('media.trakt.Trakt')
    def test_end_to_end_automatic_mode_flow(self, mock_trakt_class, mock_log, mock_notify, mock_cfg, mock_schedule_and_time):
        """Test end-to-end automatic mode flow with actual task execution."""
        mock_schedule, mock_time_module = mock_schedule_and_time
        
        # Configure intervals so tasks will be scheduled
        mock_cfg.automatic = Mock()
        mock_cfg.automatic.movies = Mock()
        mock_cfg.automatic.shows = Mock()
        mock_cfg.automatic.movies.intervals = {'public_lists': 24, 'user_lists': 12}
        mock_cfg.automatic.shows.intervals = {'public_lists': 8, 'user_lists': 6}
        
        # Configure other required config
        mock_cfg.notifications = Mock()
        mock_cfg.notifications.verbose = False  # Disable to avoid notify.send calls
        mock_cfg.filters = Mock()
        mock_cfg.filters.movies = Mock()
        mock_cfg.filters.movies.rotten_tomatoes = ""
        
        mock_time_module.time.return_value = 0
        
        # Mock Trakt to return test data
        mock_trakt = Mock()
        mock_trakt_class.return_value = mock_trakt
        
        # Define non_user_lists attribute
        mock_trakt_class.non_user_lists = ['anticipated', 'popular', 'trending', 'boxoffice']
        
        # Configure Trakt to return some test data
        mock_trakt.get_anticipated_movies.return_value = [
            {'title': 'Test Movie', 'year': 2024, 'ids': {'imdb': 'tt1234567', 'tmdb': 12345, 'trakt': 54321}}
        ]
        for method_name in ['get_popular_movies', 'get_trending_movies', 'get_boxoffice_movies', 
                           'get_watchlist_movies', 'get_user_list_movies', 'get_anticipated_shows',
                           'get_popular_shows', 'get_trending_shows', 'get_most_watched_shows',
                           'get_most_played_shows', 'get_watchlist_shows', 'get_user_list_shows']:
            getattr(mock_trakt, method_name).return_value = []
        
        # Mock schedule library
        mock_task = Mock()
        mock_task.tag = 'test_task'
        mock_task.next_run = Mock()
        mock_task.next_run.strftime.return_value = '2024-01-01 12:00:00'
        
        # Track task execution
        executed_tasks = []
        def track_task_execution(*args, **kwargs):
            executed_tasks.append(args)
            return 1  # Mock successful addition
        
        mock_task.run.side_effect = track_task_execution
        
        mock_every_hours = Mock()
        mock_every_hours.do.return_value = mock_task
        mock_schedule.every.return_value = Mock()
        mock_schedule.every.return_value.hours = mock_every_hours
        
        mock_schedule.idle_seconds.return_value = -1  # Exit immediately
        
        # Mock _process_media to avoid actual API calls
        with patch('core.business_logic._process_media') as mock_process:
            mock_process.return_value = 1  # Return number added
            
            # Limit iterations
            iteration_count = 0
            def side_effect_run_pending():
                nonlocal iteration_count
                iteration_count += 1
                if iteration_count >= 2:
                    raise KeyboardInterrupt("Test termination")
            
            mock_schedule.run_pending.side_effect = side_effect_run_pending
            
            with pytest.raises(KeyboardInterrupt):
                from core.business_logic import run_automatic_mode
                run_automatic_mode(
                    add_delay=0.1,
                    sort='votes',
                    no_search=False,
                    run_now=True,  # Execute tasks immediately
                    no_notifications=False,
                    ignore_blacklist=False
                )
        
        # Verify tasks were scheduled and executed
        assert mock_schedule.every.call_count == 4  # 4 task types
        assert mock_task.run.call_count == 4  # All tasks run immediately
        
        # Verify successful scheduling log
        mock_log.info.assert_any_call("Successfully scheduled %d automatic tasks", 4)
