#!/usr/bin/env python3
"""
Traktarr CLI Commands

This module contains all Click CLI command definitions.
The actual business logic is implemented in the core traktarr module.
"""

import click
import os
import sys

# Import the core business logic functions
from core.business_logic import (
    # Core functions
    trakt_authentication,
    add_single_show,
    add_multiple_shows,
    add_single_movie,
    add_multiple_movies,
    run_automatic_mode,
    
    # Global variables that need to be initialized
    init_globals
)


@click.group(help='Add new shows & movies to Sonarr/Radarr from Trakt.')
@click.version_option('1.2.5', prog_name='Traktarr')
@click.option(
    '--config',
    envvar='TRAKTARR_CONFIG',
    type=click.Path(file_okay=True, dir_okay=False),
    help='Configuration file',
    show_default=True,
    default=os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "config.json")
)
@click.option(
    '--cachefile',
    envvar='TRAKTARR_CACHEFILE',
    type=click.Path(file_okay=True, dir_okay=False),
    help='Cache file',
    show_default=True,
    default=os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "cache.db")
)
@click.option(
    '--logfile',
    envvar='TRAKTARR_LOGFILE',
    type=click.Path(file_okay=True, dir_okay=False),
    help='Log file',
    show_default=True,
    default=os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "activity.log")
)
def app(config, cachefile, logfile):
    """Initialize global configuration and logging."""
    init_globals(config, cachefile, logfile)


############################################################
# Trakt OAuth
############################################################

@app.command(help='Authenticate Traktarr.')
def trakt_auth():
    """Authenticate with Trakt API."""
    trakt_authentication()


############################################################
# SHOWS
############################################################

@app.command(help='Add a single show to Sonarr.', context_settings=dict(max_content_width=100))
@click.option(
    '--show-id', '-id',
    help='Trakt Show ID.',
    required=True)
@click.option(
    '--folder', '-f',
    default=None,
    help='Add show with this root folder to Sonarr.')
@click.option(
    '--no-search',
    is_flag=True,
    help='Disable search when adding show to Sonarr.')
def show(show_id, folder=None, no_search=False):
    """Add a single show to Sonarr."""
    return add_single_show(show_id, folder, no_search)


@app.command(help='Add multiple shows to Sonarr.', context_settings=dict(max_content_width=100))
@click.option(
    '--list-type', '-t',
    help='Trakt list to process. '
         'For example, \'anticipated\', \'trending\', \'popular\', \'person\', \'watched\', \'played\', '
         '\'recommended\', \'watchlist\', or any URL to a list.',
    required=True)
@click.option(
    '--add-limit', '-l',
    default=0,
    help='Limit number of shows added to Sonarr.')
@click.option(
    '--add-delay', '-d',
    default=2.5,
    help='Seconds between each add request to Sonarr.',
    show_default=True)
@click.option(
    '--sort', '-s',
    default='votes',
    type=click.Choice(['rating', 'release', 'votes']),
    help='Sort list to process.',
    show_default=True)
@click.option(
    '--years', '--year', '-y',
    default=None,
    help='Can be a specific year or a range of years to search. For example, \'2000\' or \'2000-2010\'.')
@click.option(
    '--genres', '-g',
    default=None,
    help='Only add shows from this genre to Sonarr. '
         'Multiple genres are specified as a comma-separated list. '
         'Use \'ignore\' to add shows from any genre, including ones with no genre specified.')
@click.option(
    '--folder', '-f',
    default=None,
    help='Add shows with this root folder to Sonarr.')
@click.option(
    '--person', '-p',
    default=None,
    help='Only add shows from this person (e.g. actor) to Sonarr. '
         'Only one person can be specified. '
         'Requires the \'person\' list type.')
@click.option(
    '--include-non-acting-roles',
    is_flag=True,
    help='Include non-acting roles such as \'Director\', \'As Himself\', \'Narrator\', etc. '
         'Requires the \'person\' list type with the \'person\' argument.')
@click.option(
    '--no-search',
    is_flag=True,
    help='Disable search when adding shows to Sonarr.')
@click.option(
    '--notifications',
    is_flag=True,
    help='Send notifications.')
@click.option(
    '--authenticate-user',
    help='Specify which user to authenticate with to retrieve Trakt lists. '
         'Defaults to first user in the config')
@click.option(
    '--ignore-blacklist',
    is_flag=True,
    help='Ignores the blacklist when running the command.')
@click.option(
    '--remove-rejected-from-recommended',
    is_flag=True,
    help='Removes rejected/existing shows from recommended.')
@click.option(
    '--dry-run',
    is_flag=True,
    help='Shows the list of shows remaining after processing, takes no action on them.')
def shows(
        list_type,
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
        dry_run=False,
):
    """Add multiple shows to Sonarr."""
    return add_multiple_shows(
        list_type=list_type,
        add_limit=add_limit,
        add_delay=add_delay,
        sort=sort,
        years=years,
        genres=genres,
        folder=folder,
        person=person,
        no_search=no_search,
        include_non_acting_roles=include_non_acting_roles,
        notifications=notifications,
        authenticate_user=authenticate_user,
        ignore_blacklist=ignore_blacklist,
        remove_rejected_from_recommended=remove_rejected_from_recommended,
        dry_run=dry_run,
    )


############################################################
# MOVIES
############################################################

@app.command(help='Add a single movie to Radarr.', context_settings=dict(max_content_width=100))
@click.option(
    '--movie-id', '-id',
    help='Trakt Movie ID.',
    required=True)
@click.option(
    '--folder', '-f',
    default=None,
    help='Add movie with this root folder to Radarr.')
@click.option(
    '--minimum-availability', '-ma',
    type=click.Choice(['announced', 'in_cinemas', 'released']),
    help='Add movies with this minimum availability to Radarr. Default is \'released\'.')
@click.option(
    '--no-search',
    is_flag=True,
    help='Disable search when adding movie to Radarr.')
def movie(movie_id, folder=None, minimum_availability=None, no_search=False):
    """Add a single movie to Radarr."""
    return add_single_movie(movie_id, folder, minimum_availability, no_search)


@app.command(help='Add multiple movies to Radarr.', context_settings=dict(max_content_width=100))
@click.option(
    '--list-type', '-t',
    help='Trakt list to process. '
         'For example, \'anticipated\', \'trending\', \'popular\', \'person\', \'watched\', \'played\', '
         '\'recommended\', \'watchlist\', or any URL to a list.',
    required=True)
@click.option(
    '--add-limit', '-l',
    default=0,
    help='Limit number of movies added to Radarr.')
@click.option(
    '--add-delay', '-d',
    default=2.5,
    help='Seconds between each add request to Radarr.',
    show_default=True)
@click.option(
    '--sort', '-s',
    default='votes',
    type=click.Choice(['rating', 'release', 'votes']),
    help='Sort list to process.', show_default=True)
@click.option(
    '--rotten_tomatoes', '-rt',
    default=None,
    type=int,
    help='Set a minimum Rotten Tomatoes score.')
@click.option(
    '--years', '--year', '-y',
    default=None,
    help='Can be a specific year or a range of years to search. For example, \'2000\' or \'2000-2010\'.')
@click.option(
    '--genres', '-g',
    default=None,
    help='Only add movies from this genre to Radarr. '
         'Multiple genres are specified as a comma-separated list. '
         'Use \'ignore\' to add movies from any genre, including ones with no genre specified.')
@click.option(
    '--folder', '-f',
    default=None,
    help='Add movies with this root folder to Radarr.')
@click.option(
    '--minimum-availability', '-ma',
    type=click.Choice(['announced', 'in_cinemas', 'released']),
    help='Add movies with this minimum availability to Radarr. Default is \'released\'.')
@click.option(
    '--person', '-p',
    default=None,
    help='Only add movies from this person (e.g. actor) to Radarr. '
         'Only one person can be specified. '
         'Requires the \'person\' list type.')
@click.option(
    '--include-non-acting-roles',
    is_flag=True,
    help='Include non-acting roles such as \'Director\', \'As Himself\', \'Narrator\', etc. '
         'Requires the \'person\' list type with the \'person\' argument.')
@click.option(
    '--no-search',
    is_flag=True,
    help='Disable search when adding movies to Radarr.')
@click.option(
    '--notifications',
    is_flag=True,
    help='Send notifications.')
@click.option(
    '--authenticate-user',
    help='Specify which user to authenticate with to retrieve Trakt lists. '
         'Defaults to first user in the config.')
@click.option(
    '--ignore-blacklist',
    is_flag=True,
    help='Ignores the blacklist when running the command.')
@click.option(
    '--remove-rejected-from-recommended',
    is_flag=True,
    help='Removes rejected/existing movies from recommended.')
@click.option(
    '--dry-run',
    is_flag=True,
    help='Shows the list of movies remaining after processing, takes no action on them.')
def movies(
        list_type,
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
        dry_run=False,
):
    """Add multiple movies to Radarr."""
    return add_multiple_movies(
        list_type=list_type,
        add_limit=add_limit,
        add_delay=add_delay,
        sort=sort,
        rotten_tomatoes=rotten_tomatoes,
        years=years,
        genres=genres,
        folder=folder,
        minimum_availability=minimum_availability,
        person=person,
        include_non_acting_roles=include_non_acting_roles,
        no_search=no_search,
        notifications=notifications,
        authenticate_user=authenticate_user,
        ignore_blacklist=ignore_blacklist,
        remove_rejected_from_recommended=remove_rejected_from_recommended,
        dry_run=dry_run,
    )


############################################################
# AUTOMATIC MODE
############################################################

@app.command(help='Run Traktarr in automatic mode.')
@click.option(
    '--add-delay', '-d',
    default=2.5,
    help='Seconds between each add request to Sonarr / Radarr.',
    show_default=True)
@click.option(
    '--sort', '-s',
    default='votes',
    type=click.Choice(['votes', 'rating', 'release']),
    help='Sort list to process.',
    show_default=True)
@click.option(
    '--no-search',
    is_flag=True,
    help='Disable search when adding to Sonarr / Radarr.')
@click.option(
    '--run-now',
    is_flag=True,
    help="Do a first run immediately without waiting.")
@click.option(
    '--no-notifications',
    is_flag=True,
    help="Disable notifications.")
@click.option(
    '--ignore-blacklist',
    is_flag=True,
    help='Ignores the blacklist when running the command.')
def run(
        add_delay=2.5,
        sort='votes',
        no_search=False,
        run_now=False,
        no_notifications=False,
        ignore_blacklist=False,
):
    """Run Traktarr in automatic mode."""
    return run_automatic_mode(
        add_delay=add_delay,
        sort=sort,
        no_search=no_search,
        run_now=run_now,
        no_notifications=no_notifications,
        ignore_blacklist=ignore_blacklist,
    )


if __name__ == "__main__":
    app()
