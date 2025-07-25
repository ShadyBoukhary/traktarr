"""
Test CLI Commands for Traktarr

These tests verify that CLI commands correctly parse arguments and call
the appropriate business logic functions with the correct parameters.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock

from cli.commands import app


class TestCLICommands:
    """Test all CLI commands and their argument parsing."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.runner = CliRunner()

    @patch('cli.commands.init_globals')
    def test_app_initialization_with_defaults(self, mock_init):
        """Test that the app initializes with default config paths."""
        result = self.runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert 'Add new shows & movies to Sonarr/Radarr from Trakt.' in result.output

    @patch('cli.commands.init_globals')
    def test_app_initialization_with_custom_config(self, mock_init):
        """Test app initialization with custom config file."""
        with patch('cli.commands.trakt_authentication') as mock_auth:
            result = self.runner.invoke(app, [
                '--config', '/custom/config.json',
                '--cachefile', '/custom/cache.db', 
                '--logfile', '/custom/activity.log',
                'trakt-auth'
            ])
            
            # Should initialize with custom paths
            mock_init.assert_called_once_with(
                '/custom/config.json',
                '/custom/cache.db', 
                '/custom/activity.log'
            )
            mock_auth.assert_called_once()
            assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.trakt_authentication')
    def test_trakt_auth_command(self, mock_auth, mock_init):
        """Test the trakt-auth command."""
        result = self.runner.invoke(app, ['trakt-auth'])
        
        mock_init.assert_called_once()
        mock_auth.assert_called_once()
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.add_single_show')
    def test_show_command_required_args(self, mock_add_show, mock_init):
        """Test the show command with required arguments."""
        result = self.runner.invoke(app, ['show', '--show-id', '12345'])
        
        mock_init.assert_called_once()
        mock_add_show.assert_called_once_with('12345', None, False)
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.add_single_show')
    def test_show_command_all_args(self, mock_add_show, mock_init):
        """Test the show command with all optional arguments."""
        result = self.runner.invoke(app, [
            'show',
            '--show-id', '12345',
            '--folder', '/custom/tv',
            '--no-search'
        ])
        
        mock_init.assert_called_once()
        mock_add_show.assert_called_once_with('12345', '/custom/tv', True)
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    def test_show_command_missing_required_arg(self, mock_init):
        """Test the show command fails without required show-id."""
        result = self.runner.invoke(app, ['show'])
        
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'Error' in result.output

    @patch('cli.commands.init_globals')
    @patch('cli.commands.add_multiple_shows')
    def test_shows_command_required_args(self, mock_add_shows, mock_init):
        """Test the shows command with required arguments."""
        result = self.runner.invoke(app, ['shows', '--list-type', 'trending'])
        
        mock_init.assert_called_once()
        mock_add_shows.assert_called_once_with(
            list_type='trending',
            add_limit=0,
            add_delay=2.5,
            sort='votes',
            years=None,
            genres=None,
            folder=None,
            person=None,
            no_search=False,
            include_non_acting_roles=False,
            notifications=False,
            authenticate_user=None,
            ignore_blacklist=False,
            remove_rejected_from_recommended=False,
            dry_run=False
        )
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.add_multiple_shows')
    def test_shows_command_all_args(self, mock_add_shows, mock_init):
        """Test the shows command with all arguments."""
        result = self.runner.invoke(app, [
            'shows',
            '--list-type', 'popular',
            '--add-limit', '10',
            '--add-delay', '5.0',
            '--sort', 'rating',
            '--year', '2020-2023',
            '--genres', 'drama,comedy',
            '--folder', '/custom/tv',
            '--person', 'bryan-cranston',
            '--include-non-acting-roles',
            '--no-search',
            '--notifications',
            '--authenticate-user', 'testuser',
            '--ignore-blacklist',
            '--remove-rejected-from-recommended',
            '--dry-run'
        ])
        
        mock_init.assert_called_once()
        mock_add_shows.assert_called_once_with(
            list_type='popular',
            add_limit=10,
            add_delay=5.0,
            sort='rating',
            years='2020-2023',
            genres='drama,comedy',
            folder='/custom/tv',
            person='bryan-cranston',
            no_search=True,
            include_non_acting_roles=True,
            notifications=True,
            authenticate_user='testuser',
            ignore_blacklist=True,
            remove_rejected_from_recommended=True,
            dry_run=True
        )
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.add_single_movie')
    def test_movie_command_required_args(self, mock_add_movie, mock_init):
        """Test the movie command with required arguments."""
        result = self.runner.invoke(app, ['movie', '--movie-id', '67890'])
        
        mock_init.assert_called_once()
        mock_add_movie.assert_called_once_with('67890', None, None, False)
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.add_single_movie')
    def test_movie_command_all_args(self, mock_add_movie, mock_init):
        """Test the movie command with all optional arguments."""
        result = self.runner.invoke(app, [
            'movie',
            '--movie-id', '67890',
            '--folder', '/custom/movies',
            '--minimum-availability', 'in_cinemas',
            '--no-search'
        ])
        
        mock_init.assert_called_once()
        mock_add_movie.assert_called_once_with('67890', '/custom/movies', 'in_cinemas', True)
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.add_multiple_movies')
    def test_movies_command_required_args(self, mock_add_movies, mock_init):
        """Test the movies command with required arguments."""
        result = self.runner.invoke(app, ['movies', '--list-type', 'anticipated'])
        
        mock_init.assert_called_once()
        mock_add_movies.assert_called_once_with(
            list_type='anticipated',
            add_limit=0,
            add_delay=2.5,
            sort='votes',
            rotten_tomatoes=None,
            years=None,
            genres=None,
            folder=None,
            minimum_availability=None,
            person=None,
            include_non_acting_roles=False,
            no_search=False,
            notifications=False,
            authenticate_user=None,
            ignore_blacklist=False,
            remove_rejected_from_recommended=False,
            dry_run=False
        )
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.add_multiple_movies')
    def test_movies_command_all_args(self, mock_add_movies, mock_init):
        """Test the movies command with all arguments."""
        result = self.runner.invoke(app, [
            'movies',
            '--list-type', 'trending',
            '--add-limit', '5',
            '--add-delay', '3.0',
            '--sort', 'release',
            '--rotten_tomatoes', '80',
            '--years', '2022',
            '--genres', 'action,thriller',
            '--folder', '/custom/movies',
            '--minimum-availability', 'released',
            '--person', 'tom-cruise',
            '--include-non-acting-roles',
            '--no-search',
            '--notifications',
            '--authenticate-user', 'movieuser',
            '--ignore-blacklist',
            '--remove-rejected-from-recommended',
            '--dry-run'
        ])
        
        mock_init.assert_called_once()
        mock_add_movies.assert_called_once_with(
            list_type='trending',
            add_limit=5,
            add_delay=3.0,
            sort='release',
            rotten_tomatoes=80,
            years='2022',
            genres='action,thriller',
            folder='/custom/movies',
            minimum_availability='released',
            person='tom-cruise',
            include_non_acting_roles=True,
            no_search=True,
            notifications=True,
            authenticate_user='movieuser',
            ignore_blacklist=True,
            remove_rejected_from_recommended=True,
            dry_run=True
        )
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.run_automatic_mode')
    def test_run_command_default_args(self, mock_run, mock_init):
        """Test the run command with default arguments."""
        result = self.runner.invoke(app, ['run'])
        
        mock_init.assert_called_once()
        mock_run.assert_called_once_with(
            add_delay=2.5,
            sort='votes',
            no_search=False,
            run_now=False,
            no_notifications=False,
            ignore_blacklist=False
        )
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    @patch('cli.commands.run_automatic_mode')
    def test_run_command_all_args(self, mock_run, mock_init):
        """Test the run command with all arguments."""
        result = self.runner.invoke(app, [
            'run',
            '--add-delay', '1.0',
            '--sort', 'rating',
            '--no-search',
            '--run-now',
            '--no-notifications',
            '--ignore-blacklist'
        ])
        
        mock_init.assert_called_once()
        mock_run.assert_called_once_with(
            add_delay=1.0,
            sort='rating',
            no_search=True,
            run_now=True,
            no_notifications=True,
            ignore_blacklist=True
        )
        assert result.exit_code == 0

    @patch('cli.commands.init_globals')
    def test_shows_command_missing_required_arg(self, mock_init):
        """Test the shows command fails without required list-type."""
        result = self.runner.invoke(app, ['shows'])
        
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'Error' in result.output

    @patch('cli.commands.init_globals')
    def test_movies_command_missing_required_arg(self, mock_init):
        """Test the movies command fails without required list-type."""
        result = self.runner.invoke(app, ['movies'])
        
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'Error' in result.output

    @patch('cli.commands.init_globals')
    def test_movie_command_missing_required_arg(self, mock_init):
        """Test the movie command fails without required movie-id."""
        result = self.runner.invoke(app, ['movie'])
        
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'Error' in result.output

    def test_invalid_sort_option_shows(self):
        """Test that invalid sort options are rejected for shows command."""
        result = self.runner.invoke(app, ['shows', '--list-type', 'trending', '--sort', 'invalid'])
        
        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'Error' in result.output

    def test_invalid_sort_option_movies(self):
        """Test that invalid sort options are rejected for movies command."""
        result = self.runner.invoke(app, ['movies', '--list-type', 'trending', '--sort', 'invalid'])
        
        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'Error' in result.output

    def test_invalid_sort_option_run(self):
        """Test that invalid sort options are rejected for run command."""
        result = self.runner.invoke(app, ['run', '--sort', 'invalid'])
        
        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'Error' in result.output

    def test_invalid_minimum_availability_movie(self):
        """Test that invalid minimum availability options are rejected for movie command."""
        result = self.runner.invoke(app, ['movie', '--movie-id', '123', '--minimum-availability', 'invalid'])
        
        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'Error' in result.output

    def test_invalid_minimum_availability_movies(self):
        """Test that invalid minimum availability options are rejected for movies command."""
        result = self.runner.invoke(app, ['movies', '--list-type', 'trending', '--minimum-availability', 'invalid'])
        
        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'Error' in result.output

    @patch('cli.commands.init_globals')
    def test_help_output_contains_expected_commands(self, mock_init):
        """Test that help output contains all expected commands."""
        result = self.runner.invoke(app, ['--help'])
        
        assert result.exit_code == 0
        assert 'trakt-auth' in result.output
        assert 'show' in result.output
        assert 'shows' in result.output
        assert 'movie' in result.output
        assert 'movies' in result.output
        assert 'run' in result.output

    @patch('cli.commands.init_globals') 
    def test_command_help_shows_options(self, mock_init):
        """Test that command help shows all available options."""
        result = self.runner.invoke(app, ['shows', '--help'])
        
        assert result.exit_code == 0
        assert '--list-type' in result.output
        assert '--add-limit' in result.output
        assert '--add-delay' in result.output
        assert '--sort' in result.output
        assert '--dry-run' in result.output
        assert '--notifications' in result.output
