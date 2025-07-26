#!/usr/bin/env python3
"""
Traktarr Core Module

This module contains the core business logic for Traktarr.
CLI commands are defined in cli/commands.py and call these functions.
"""

import os.path
import signal
import sys
import time

import schedule

############################################################
# INIT
############################################################
cfg = None
log = None
notify = None
app_loaded = False


def init_globals(config_path, cachefile_path, logfile_path):
    """Initialize global configuration, logging, and notifications."""
    global cfg, log, notify, app_loaded

    # Load config FIRST
    from misc.config import Config
    cfg = Config(configfile=config_path, cachefile=cachefile_path, logfile=logfile_path).cfg
    
    # Legacy Support
    if cfg.filters.movies.blacklist_title_keywords:
        cfg['filters']['movies']['blacklisted_title_keywords'] = cfg['filters']['movies']['blacklist_title_keywords']
    if cfg.filters.movies.rating_limit:
        cfg['filters']['movies']['rotten_tomatoes'] = cfg['filters']['movies']['rating_limit']
    if cfg.radarr.profile:
        cfg['radarr']['quality'] = cfg['radarr']['profile']
    if cfg.sonarr.profile:
        cfg['sonarr']['quality'] = cfg['sonarr']['profile']

    # Load logger AFTER config is initialized
    from misc.log import logger
    log = logger.get_logger('Traktarr')

    # Load notifications
    from notifications import Notifications
    notify = Notifications()

    # Initialize notifications
    app_loaded = True
    init_notifications()


############################################################
# VALIDATION & HELPERS
############################################################

def validate_trakt(trakt, notifications):
    log.info("Validating Trakt API Key...")
    if not trakt.validate_client_id():
        log.error("Aborting due to failure to validate Trakt API Key")
        if notifications:
            callback_notify({
                'event': 'error',
                'reason': 'Failure to validate Trakt API Key'
            })
        exit()
    else:
        log.info("...Validated Trakt API Key.")


def validate_pvr(pvr, pvr_type, notifications):
    if not pvr.validate_api_key():
        log.error("Aborting due to failure to validate %s URL / API Key", pvr_type)
        if notifications:
            callback_notify({
                'event': 'error',
                'reason': f'Failure to validate {pvr_type} URL / API Key'
            })
        return None
    else:
        log.info("Validated %s URL & API Key.", pvr_type)


def get_quality_profile_id(pvr, quality_profile):
    # retrieve profile id for requested quality profile
    quality_profile_id = pvr.get_quality_profile_id(quality_profile)
    if not quality_profile_id or quality_profile_id <= 0:
        log.error("Aborting due to failure to retrieve Quality Profile ID for: %s", quality_profile)
        exit()
    log.info("Retrieved Quality Profile ID for \'%s\': %d", quality_profile, quality_profile_id)
    return quality_profile_id


def get_language_profile_id(pvr, language_profile):
    # retrieve profile id for requested language profile
    language_profile_id = pvr.get_language_profile_id(language_profile)
    if not language_profile_id or language_profile_id <= 0:
        log.error("No Language Profile ID for: %s", language_profile)
    else:
        log.info("Retrieved Language Profile ID for \'%s\': %d", language_profile, language_profile_id)
    return language_profile_id


def get_profile_tags(pvr):
    profile_tags = pvr.get_tags()
    if profile_tags is None:
        log.error("Aborting due to failure to retrieve Tag IDs")
        exit()
    log.info("Retrieved Sonarr Tag IDs: %d", len(profile_tags))
    return profile_tags


def get_objects(pvr, pvr_type, notifications):
    objects_list = pvr.get_objects()
    objects_type = 'movies' if pvr_type.lower() == 'radarr' else 'shows'
    if not objects_list:
        log.error("Aborting due to failure to retrieve %s list from %s", objects_type, pvr_type)
        if notifications:
            callback_notify({
                'event': 'error',
                'reason': f'Failure to retrieve {objects_type} list from {pvr_type}'
            })
        exit()
    log.info("Retrieved %s %s list, %s found: %d", pvr_type, objects_type, objects_type, len(objects_list))
    return objects_list


def get_exclusions(pvr, pvr_type):
    objects_list = pvr.get_exclusions()
    objects_type = 'movie' if pvr_type.lower() == 'radarr' else 'show'
    if not objects_list:
        log.info("No %s exclusions list found from %s", objects_type, pvr_type)
    log.info("Retrieved %s %s list, %s found: %d", pvr_type, objects_type, objects_type, len(objects_list))
    return objects_list


def _get_trakt_list(trakt, media_type, list_type, person, include_non_acting_roles, authenticate_user, years, countries, languages, genres, runtimes):
    """
    Get the appropriate Trakt list based on media type and list type.
    
    Args:
        trakt: Trakt instance
        media_type: 'shows' or 'movies'
        list_type: Type of list to retrieve
        person: Person name for person lists
        include_non_acting_roles: Include non-acting roles for person lists
        authenticate_user: User to authenticate for certain lists
        years: Year filter
        countries: Country filter
        languages: Language filter
        genres: Genre filter
        runtimes: Runtime filter (movies only)
    
    Returns:
        List of Trakt objects or None if failed
    """
    from helpers import misc as misc_helper
    
    if media_type == 'shows':
        if list_type.lower() == 'anticipated':
            return trakt.get_anticipated_shows(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
            )
        elif list_type.lower() == 'trending':
            return trakt.get_trending_shows(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
            )
        elif list_type.lower() == 'popular':
            return trakt.get_popular_shows(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
            )
        elif list_type.lower() == 'person':
            if not person:
                log.error("Person argument required when using person list type.")
                return None
            return trakt.get_person_shows(
                person=person,
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
                include_non_acting_roles=include_non_acting_roles,
            )
        elif list_type.lower() == 'recommended':
            return trakt.get_recommended_shows(
                authenticate_user,
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
            )
        elif list_type.lower().startswith('played'):
            most_type = misc_helper.substring_after(list_type.lower(), "_")
            return trakt.get_most_played_shows(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
                most_type=most_type if most_type else None,
            )
        elif list_type.lower().startswith('watched'):
            most_type = misc_helper.substring_after(list_type.lower(), "_")
            return trakt.get_most_watched_shows(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
                most_type=most_type if most_type else None,
            )
        elif list_type.lower() == 'watchlist':
            return trakt.get_watchlist_shows(authenticate_user)
        else:
            return trakt.get_user_list_shows(list_type, authenticate_user)
    
    elif media_type == 'movies':
        if list_type.lower() == 'anticipated':
            return trakt.get_anticipated_movies(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
                runtimes=runtimes,
            )
        elif list_type.lower() == 'trending':
            return trakt.get_trending_movies(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
                runtimes=runtimes,
            )
        elif list_type.lower() == 'popular':
            return trakt.get_popular_movies(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
                runtimes=runtimes,
            )
        elif list_type.lower() == 'boxoffice':
            return trakt.get_boxoffice_movies()
        elif list_type.lower() == 'person':
            if not person:
                log.error("Person argument required when using person list type.")
                return None
            return trakt.get_person_movies(
                years=years,
                person=person,
                countries=countries,
                languages=languages,
                genres=genres,
                runtimes=runtimes,
                include_non_acting_roles=include_non_acting_roles,
            )
        elif list_type.lower() == 'recommended':
            return trakt.get_recommended_movies(
                authenticate_user,
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
                runtimes=runtimes,
            )
        elif list_type.lower().startswith('played'):
            most_type = misc_helper.substring_after(list_type.lower(), "_")
            return trakt.get_most_played_movies(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
                runtimes=runtimes,
                most_type=most_type if most_type else None,
            )
        elif list_type.lower().startswith('watched'):
            most_type = misc_helper.substring_after(list_type.lower(), "_")
            return trakt.get_most_watched_movies(
                years=years,
                countries=countries,
                languages=languages,
                genres=genres,
                runtimes=runtimes,
                most_type=most_type if most_type else None,
            )
        elif list_type.lower() == 'watchlist':
            return trakt.get_watchlist_movies(authenticate_user)
        else:
            return trakt.get_user_list_movies(list_type, authenticate_user)
    
    return None


############################################################
# Common Media Processing Function
############################################################
def _process_media(
        media_type,
        list_type,
        add_limit=0,
        add_delay=2.5,
        sort='votes',
        years=None,
        genres=None,
        folder=None,
        person=None,
        include_non_acting_roles=False,
        no_search=False,
        notifications=False,
        authenticate_user=None,
        ignore_blacklist=False,
        remove_rejected_from_recommended=False,
        dry_run=False,
        rotten_tomatoes=None,
        minimum_availability=None,
):
    """
    Common function for processing both shows and movies from Trakt lists.
    
    Args:
        media_type: 'shows' or 'movies'
        list_type: Type of Trakt list to process
        add_limit: Maximum number of items to add
        add_delay: Seconds between each add request
        sort: Sort method for lists
        years: Year filter
        genres: Genre filter
        folder: Root folder override
        person: Person name for person lists
        include_non_acting_roles: Include non-acting roles for person lists
        no_search: Disable search when adding
        notifications: Send notifications
        authenticate_user: User to authenticate for certain lists
        ignore_blacklist: Ignore blacklist filters
        remove_rejected_from_recommended: Remove rejected items from recommended list
        dry_run: Show what would be added without adding
        rotten_tomatoes: Minimum RT score (movies only)
        minimum_availability: Minimum availability (movies only)
    
    Returns:
        Number of items added
    """
    from helpers import misc as misc_helper
    from helpers import parameter as parameter_helper
    from helpers import omdb as omdb_helper
    from helpers import tmdb as tmdb_helper
    from helpers import trakt as trakt_helper
    
    # Configure based on media type
    if media_type == 'shows':
        from media.sonarr import Sonarr
        from helpers import sonarr as pvr_helper
        
        pvr_class = Sonarr
        pvr_config = cfg.sonarr
        pvr_name = 'Sonarr'
        config_key = 'shows'
        filters_config = cfg.filters.shows
        media_key = 'show'
        media_name = 'show'
        media_plural = 'shows'
        add_func_name = 'add_show'
        event_name = 'add_show'
        validate_func = tmdb_helper.check_show_tmdb_id if hasattr(tmdb_helper, 'check_show_tmdb_id') else None
    elif media_type == 'movies':
        from media.radarr import Radarr
        from helpers import radarr as pvr_helper
        
        pvr_class = Radarr
        pvr_config = cfg.radarr
        pvr_name = 'Radarr'
        config_key = 'movies'
        filters_config = cfg.filters.movies
        media_key = 'movie'
        media_name = 'movie'
        media_plural = 'movies'
        add_func_name = 'add_movie'
        event_name = 'add_movie'
        validate_func = tmdb_helper.check_movie_tmdb_id
    else:
        raise ValueError(f"Invalid media_type: {media_type}. Must be 'shows' or 'movies'")
    
    from media.trakt import Trakt
    
    added_count = 0

    # Process countries
    if not getattr(filters_config, 'allowed_countries', None) or 'ignore' in getattr(filters_config, 'allowed_countries', []):
        countries = None
    else:
        countries = filters_config.allowed_countries

    # Process languages
    if not getattr(filters_config, 'allowed_languages', None) or 'ignore' in getattr(filters_config, 'allowed_languages', []):
        languages = None
    else:
        languages = filters_config.allowed_languages

    # Process genres
    if genres:
        # Split comma separated list
        genres = sorted(genres.split(','), key=str.lower)

        # Look for special keyword 'ignore'
        if 'ignore' in genres:
            # Set special keyword 'ignore' to media's blacklisted_genres list
            cfg['filters'][config_key]['blacklisted_genres'] = ['ignore']
            # Set genre search parameter to None
            genres = None
        else:
            # Remove genre from media's blacklisted_genres list, if it's there
            misc_helper.unblacklist_genres(genres, cfg['filters'][config_key]['blacklisted_genres'])
            log.debug("Filter Trakt results with genre(s): %s", ', '.join(map(lambda x: x.title(), genres)))

    # Process years parameter
    years, new_min_year, new_max_year = parameter_helper.years(
        years,
        getattr(filters_config, 'blacklisted_min_year', None),
        getattr(filters_config, 'blacklisted_max_year', None),
    )

    cfg['filters'][config_key]['blacklisted_min_year'] = new_min_year
    cfg['filters'][config_key]['blacklisted_max_year'] = new_max_year

    # Runtime range (movies only)
    runtimes = None
    if media_type == 'movies':
        if getattr(filters_config, 'blacklisted_min_runtime', None):
            min_runtime = filters_config.blacklisted_min_runtime
        else:
            min_runtime = 0

        if getattr(filters_config, 'blacklisted_max_runtime', None) and filters_config.blacklisted_max_runtime >= min_runtime:
            max_runtime = filters_config.blacklisted_max_runtime
        else:
            max_runtime = 9999

        if min_runtime == 0 and max_runtime == 9999:
            runtimes = None
        else:
            runtimes = str(min_runtime) + '-' + str(max_runtime)

    # Replace root_folder if folder is supplied
    if folder:
        cfg[config_key]['root_folder'] = folder
    log.debug('Set root folder to: \'%s\'', pvr_config.root_folder)

    # Movies-specific: replace minimum_availability if supplied
    if media_type == 'movies' and minimum_availability:
        valid_min_avail = ['announced', 'in_cinemas', 'released']
        if minimum_availability:
            cfg['radarr']['minimum_availability'] = minimum_availability
        elif cfg['radarr']['minimum_availability'] not in valid_min_avail:
            cfg['radarr']['minimum_availability'] = 'released'
        log.debug('Set minimum availability to: \'%s\'', cfg['radarr']['minimum_availability'])

    # Validate trakt api_key
    trakt = Trakt(cfg)
    pvr = pvr_class(pvr_config.url, pvr_config.api_key)

    validate_trakt(trakt, notifications)
    validate_pvr(pvr, pvr_name, notifications)

    # Quality profile id
    quality_profile_id = get_quality_profile_id(pvr, getattr(pvr_config, 'quality', None))

    pvr_objects_list = get_objects(pvr, pvr_name, notifications)
    
    # Get exclusions list (only for movies, Sonarr doesn't support exclusions)
    if media_type == 'movies':
        pvr_exclusions_list = get_exclusions(pvr, pvr_name)
    else:
        pvr_exclusions_list = None

    # Get trakt list
    trakt_objects_list = _get_trakt_list(
        trakt, media_type, list_type, person, include_non_acting_roles, 
        authenticate_user, years, countries, languages, genres, runtimes
    )

    if not trakt_objects_list:
        log.error("Aborting due to failure to retrieve Trakt '%s' %s list.", list_type.capitalize(), media_plural)
        if notifications:
            callback_notify({
                'event': 'abort', 
                'type': media_plural, 
                'list_type': list_type,
                'reason': f"Failure to retrieve Trakt '{list_type.capitalize()}' {media_plural} list."
            })
        return None
    else:
        log.info("Retrieved Trakt '%s' %s list, %s found: %d", list_type.capitalize(), media_plural, media_plural, len(trakt_objects_list))

    # Set remove_rejected_recommended to False if this is not the recommended list
    if list_type.lower() != 'recommended':
        remove_rejected_from_recommended = False

    # Build filtered list without items that exist in PVR
    if media_type == 'shows':
        # Shows only support removing existing items, not exclusions
        processed_list = pvr_helper.remove_existing_series_from_trakt_list(
            pvr_objects_list,
            trakt_objects_list,
            callback_remove_recommended if remove_rejected_from_recommended else None
        )
        removal_successful = processed_list is not None
    else:  # movies
        # Movies support both existing and excluded items
        processed_list, removal_successful = pvr_helper.remove_existing_and_excluded_movies_from_trakt_list(
            pvr_objects_list,
            pvr_exclusions_list,
            trakt_objects_list,
            callback_remove_recommended if remove_rejected_from_recommended else None
        )

    if processed_list is None:
        if not removal_successful:
            log.error("Aborting due to failure to remove existing %s %s from retrieved Trakt %s list.", pvr_name, media_plural, media_plural)
            if notifications:
                callback_notify({
                    'event': 'abort', 
                    'type': media_plural, 
                    'list_type': list_type,
                    'reason': f"Failure to remove existing {pvr_name} {media_plural} from retrieved Trakt '{list_type.capitalize()}' {media_plural} list."
                })
        else:
            log.info("No more %s left to process in '%s' %s list.", media_plural, list_type.capitalize(), media_plural)
        return None
    else:
        if media_type == 'movies':
            log.info("Removed existing and excluded %s %s from Trakt %s list. %s left to process: %d", 
                    pvr_name, media_plural, media_plural, media_plural.capitalize(), len(processed_list))
        else:
            log.info("Removed existing %s %s from Trakt %s list. %s left to process: %d", 
                    pvr_name, media_plural, media_plural, media_plural.capitalize(), len(processed_list))

    # Sort filtered list
    if sort == 'release':
        sorted_list = misc_helper.sorted_list(processed_list, media_key, 'released')
        log.info("Sorted %s list to process by recent 'release' date.", media_plural)
    elif sort == 'rating':
        sorted_list = misc_helper.sorted_list(processed_list, media_key, 'rating')
        log.info("Sorted %s list to process by highest 'rating'.", media_plural)
    else:
        sorted_list = misc_helper.sorted_list(processed_list, media_key, 'votes')
        log.info("Sorted %s list to process by highest 'votes'.", media_plural)

    # Display specified min RT score (movies only)
    if media_type == 'movies' and rotten_tomatoes is not None:
        if cfg.omdb.api_key:
            log.info("Minimum Rotten Tomatoes score of %d%% requested.", rotten_tomatoes)
        else:
            log.info("Skipping minimum Rotten Tomatoes score check as OMDb API Key is missing.")

    # Process the list
    log.info("Processing list now...")
    for sorted_item in sorted_list:
        # noinspection PyBroadException

        # Set common variables
        item_title = sorted_item[media_key]['title']
        item_tmdb_id = sorted_item[media_key]['ids']['tmdb']
        item_imdb_id = sorted_item[media_key]['ids']['imdb']

        # Convert year to string
        item_year = str(sorted_item[media_key]['year']) if sorted_item[media_key]['year'] else '????'

        # Build list of genres
        item_genres = (', '.join(sorted_item[media_key]['genres'])).title() if sorted_item[media_key]['genres'] else 'N/A'

        try:
            # Check if item has a valid TMDb ID and that it exists on TMDb
            if validate_func and not validate_func(item_title, item_year, item_tmdb_id):
                continue

            # Check if genres matches genre(s) supplied via argument
            if genres and not misc_helper.allowed_genres(genres, media_key, sorted_item):
                log.debug("SKIPPING: '%s (%s)' because it was not from the genre(s): %s", 
                         item_title, item_year, ', '.join(map(lambda x: x.title(), genres)))
                continue

            # Check if item passes blacklist criteria inspection
            if media_type == 'shows':
                is_blacklisted = trakt_helper.is_show_blacklisted(
                    sorted_item,
                    filters_config,
                    ignore_blacklist,
                    callback_remove_recommended if remove_rejected_from_recommended else None,
                )
            else:  # movies
                is_blacklisted = trakt_helper.is_movie_blacklisted(
                    sorted_item,
                    filters_config,
                    ignore_blacklist,
                    callback_remove_recommended if remove_rejected_from_recommended else None,
                )

            if not is_blacklisted:
                # Skip movie if below user specified min RT score (movies only)
                if media_type == 'movies' and rotten_tomatoes is not None and cfg.omdb.api_key:
                    if not omdb_helper.does_movie_have_min_req_rt_score(
                            cfg.omdb.api_key,
                            item_title,
                            item_year,
                            item_imdb_id,
                            rotten_tomatoes,
                    ):
                        continue

                log.info("ADDING: '%s (%s)' | Country: %s | Language: %s | Genre(s): %s ",
                         item_title,
                         item_year,
                         (sorted_item[media_key]['country'] or 'N/A').upper(),
                         (sorted_item[media_key]['language'] or 'N/A').upper(),
                         item_genres,
                         )

                if dry_run:
                    log.info("dry-run: SKIPPING")
                else:
                    # Add item to PVR
                    if media_type == 'shows':
                        # Language profile id
                        language_profile_id = get_language_profile_id(pvr, cfg.sonarr.language)
                        
                        # Profile tags
                        profile_tags = None
                        tag_ids = None
                        
                        if cfg.sonarr.tags is not None:
                            from helpers import sonarr as sonarr_helper
                            profile_tags = get_profile_tags(pvr)
                            if profile_tags is not None:
                                tag_ids = sonarr_helper.series_tag_ids_list_builder(
                                    profile_tags,
                                    cfg.sonarr.tags,
                                )
                        
                        # Series type
                        if any('anime' in s.lower() for s in sorted_item[media_key]['genres']):
                            series_type = 'anime'
                        else:
                            series_type = 'standard'
                        
                        add_result = pvr.add_series(
                            sorted_item[media_key]['ids']['tvdb'],
                            sorted_item[media_key]['title'],
                            sorted_item[media_key]['ids']['slug'],
                            quality_profile_id,
                            language_profile_id,
                            cfg.sonarr.root_folder,
                            cfg.sonarr.season_folder,
                            tag_ids,
                            not no_search,
                            series_type,
                        )
                    else:  # movies
                        add_result = pvr.add_movie(
                            sorted_item[media_key]['ids']['tmdb'],
                            sorted_item[media_key]['title'],
                            sorted_item[media_key]['year'],
                            sorted_item[media_key]['ids']['slug'],
                            quality_profile_id,
                            cfg.radarr.root_folder,
                            cfg.radarr.minimum_availability,
                            not no_search,
                        )

                    if add_result:
                        if notifications:
                            callback_notify({
                                'event': event_name,
                                media_key: sorted_item[media_key],
                                'list_type': list_type
                            })
                        added_count += 1
                    else:
                        log.error("FAILED ADDING: '%s (%s)'", item_title, item_year)
                        continue
            else:
                log.info("SKIPPED: '%s (%s)'", item_title, item_year)
                continue

            # Stop adding items, if added_count >= add_limit
            if add_limit and added_count >= add_limit:
                break

            # Sleep before adding any more
            time.sleep(add_delay)

        except Exception:
            log.exception("Exception while processing %s '%s': ", media_name, item_title)

    log.info("Added %d new %s(s) to %s", added_count, media_name, pvr_name)

    # Send notification
    if notifications and (cfg.notifications.verbose or added_count > 0):
        notify.send(message=f"Added {added_count} {media_name}(s) from Trakt's '{list_type.capitalize()}' list")

    return added_count


############################################################
# CLI INTERFACE FUNCTIONS
############################################################

def trakt_authentication():
    """Authenticate with Trakt API."""
    from media.trakt import Trakt
    trakt = Trakt(cfg)

    if trakt.oauth_authentication():
        log.info("Authentication completed successfully.")
    else:
        log.error("Authentication failed.")


def add_single_show(show_id, folder=None, no_search=False):
    """Add a single show to Sonarr."""
    from media.sonarr import Sonarr
    from media.trakt import Trakt
    from helpers import sonarr as sonarr_helper
    from helpers import str as misc_str

    # replace sonarr root_folder if folder is supplied
    if folder:
        cfg['sonarr']['root_folder'] = folder

    trakt = Trakt(cfg)
    sonarr = Sonarr(cfg.sonarr.url, cfg.sonarr.api_key)

    validate_trakt(trakt, False)
    validate_pvr(sonarr, 'Sonarr', False)

    # get trakt show
    trakt_show = trakt.get_show(show_id)

    if not trakt_show:
        log.error("Aborting due to failure to retrieve Trakt show")
        return None

    # set common series variables
    series_title = trakt_show['title']

    # convert series year to string
    if trakt_show['year']:
        series_year = str(trakt_show['year'])
    elif trakt_show['first_aired']:
        series_year = misc_str.get_year_from_timestamp(trakt_show['first_aired'])
    else:
        series_year = '????'

    log.info("Retrieved Trakt show information for \'%s\': \'%s (%s)\'", show_id, series_title, series_year)

    # quality profile id
    quality_profile_id = get_quality_profile_id(sonarr, cfg.sonarr.quality)

    # language profile id
    language_profile_id = get_language_profile_id(sonarr, cfg.sonarr.language)

    # profile tags
    profile_tags = None
    tag_ids = None
    tag_names = None

    if cfg.sonarr.tags is not None:
        profile_tags = get_profile_tags(sonarr)
        if profile_tags is not None:
            # determine which tags to use when adding this series
            tag_ids = sonarr_helper.series_tag_ids_list_builder(
                profile_tags,
                cfg.sonarr.tags,
            )
            tag_names = sonarr_helper.series_tag_names_list_builder(
                profile_tags,
                tag_ids,
            )

    # series type
    if any('anime' in s.lower() for s in trakt_show['genres']):
        series_type = 'anime'
    else:
        series_type = 'standard'

    log.debug("Set series type for \'%s (%s)\' to: %s", series_title, series_year, series_type.title())

    # add show to sonarr
    if sonarr.add_series(
            trakt_show['ids']['tvdb'],
            series_title,
            trakt_show['ids']['slug'],
            quality_profile_id,
            language_profile_id,
            cfg.sonarr.root_folder,
            cfg.sonarr.season_folder,
            tag_ids,
            not no_search,
            series_type,
    ):

        if profile_tags is not None and tag_names is not None:
            log.info("ADDED: \'%s (%s)\' with Sonarr Tags: %s", series_title, series_year,
                     tag_names)
        else:
            log.info("ADDED: \'%s (%s)\'", series_title, series_year)
    elif profile_tags is not None:
        log.error("FAILED ADDING: \'%s (%s)\' with Sonarr Tags: %s", series_title, series_year,
                  tag_names)
    else:
        log.info("FAILED ADDING: \'%s (%s)\'", series_title, series_year)

    return


def add_multiple_shows(**kwargs):
    """Add multiple shows to Sonarr."""
    return _process_media('shows', **kwargs)


def add_single_movie(movie_id, folder=None, minimum_availability=None, no_search=False):
    """Add a single movie to Radarr."""
    from media.radarr import Radarr
    from media.trakt import Trakt

    # replace radarr root_folder if folder is supplied
    if folder:
        cfg['radarr']['root_folder'] = folder
    log.debug('Set root folder to: \'%s\'', cfg['radarr']['root_folder'])

    # replace radarr.minimum_availability if minimum_availability is supplied
    valid_min_avail = ['announced', 'in_cinemas', 'released']

    if minimum_availability:
        cfg['radarr']['minimum_availability'] = minimum_availability
    elif cfg['radarr']['minimum_availability'] not in valid_min_avail:
        cfg['radarr']['minimum_availability'] = 'released'

    log.debug('Set minimum availability to: \'%s\'', cfg['radarr']['minimum_availability'])

    # validate trakt api_key
    trakt = Trakt(cfg)
    radarr = Radarr(cfg.radarr.url, cfg.radarr.api_key)

    validate_trakt(trakt, False)
    validate_pvr(radarr, 'Radarr', False)

    # quality profile id
    quality_profile_id = get_quality_profile_id(radarr, cfg.radarr.quality)

    # get trakt movie
    trakt_movie = trakt.get_movie(movie_id)

    if not trakt_movie:
        log.error("Aborting due to failure to retrieve Trakt movie")
        return None

    # convert movie year to string
    movie_year = str(trakt_movie['year']) if trakt_movie['year'] else '????'

    log.info("Retrieved Trakt movie information for \'%s\': \'%s (%s)\'", movie_id, trakt_movie['title'], movie_year)

    # add movie to radarr
    if radarr.add_movie(
            trakt_movie['ids']['tmdb'],
            trakt_movie['title'],
            trakt_movie['year'],
            trakt_movie['ids']['slug'],
            quality_profile_id,
            cfg.radarr.root_folder,
            cfg.radarr.minimum_availability,
            not no_search,
    ):

        log.info("ADDED \'%s (%s)\'", trakt_movie['title'], movie_year)
    else:
        log.error("FAILED ADDING \'%s (%s)\'", trakt_movie['title'], movie_year)

    return


def add_multiple_movies(**kwargs):
    """Add multiple movies to Radarr."""
    return _process_media('movies', **kwargs)


############################################################
# CALLBACKS
############################################################

def callback_remove_recommended(media_type, media_info):
    from media.trakt import Trakt

    trakt = Trakt(cfg)

    if not media_info[media_type]['title'] or not media_info[media_type]['year']:
        log.debug("Skipping removing %s item from recommended list as no title/year was available:\n%s", media_type,
                  media_info)
        return

    # convert media year to string
    media_year = str(media_info[media_type]['year']) if media_info[media_type]['year'] else '????'

    media_name = '\'%s (%s)\'' % (media_info[media_type]['title'], media_year)

    if trakt.remove_recommended_item(media_type, media_info[media_type]['ids']['trakt']):
        log.info("Removed rejected recommended %s: \'%s\'", media_type, media_name)
    else:
        log.info("FAILED removing rejected recommended %s: \'%s\'", media_type, media_name)


def callback_notify(data):
    log.debug("Received callback data: %s", data)

    # handle event
    if data['event'] == 'add_movie':

        # convert movie year to string
        movie_year = str(data['movie']['year']) \
            if data['movie']['year'] else '????'

        if cfg.notifications.verbose:
            notify.send(
                message="Added \'%s\' movie: \'%s (%s)\'" % (data['list_type'].capitalize(), data['movie']['title'],
                                                             movie_year))
        return
    elif data['event'] == 'add_show':

        # convert series year to string
        series_year = str(data['show']['year']) if data['show']['year'] else '????'

        if cfg.notifications.verbose:
            notify.send(
                message="ADDED \'%s\' show: \'%s (%s)\'" % (data['list_type'].capitalize(), data['show']['title'],
                                                            series_year))
        return
    elif data['event'] == 'abort':
        notify.send(message="ABORTED ADDING Trakt \'%s\' %s due to: %s" % (data['list_type'].capitalize(), data['type'],
                                                                           data['reason']))
        return
    elif data['event'] == 'error':
        notify.send(message="Error: %s" % data['reason'])
        return
    else:
        log.error("Unexpected callback: %s", data)
    return


############################################################
# AUTOMATIC FUNCTIONS
############################################################

def automatic_shows(
        add_delay=2.5,
        sort='votes',
        no_search=False,
        notifications=False,
        ignore_blacklist=False,
):
    return _automatic_media(
        'shows',
        add_delay=add_delay,
        sort=sort,
        no_search=no_search,
        notifications=notifications,
        ignore_blacklist=ignore_blacklist
    )


def automatic_movies(
        add_delay=2.5,
        sort='votes',
        no_search=False,
        notifications=False,
        ignore_blacklist=False,
        rotten_tomatoes=None,
):
    return _automatic_media(
        'movies',
        add_delay=add_delay,
        sort=sort,
        no_search=no_search,
        notifications=notifications,
        ignore_blacklist=ignore_blacklist,
        rotten_tomatoes=rotten_tomatoes
    )


def automatic_shows_public_lists(
        add_delay=2.5,
        sort='votes',
        no_search=False,
        notifications=False,
        ignore_blacklist=False,
):
    return _automatic_media(
        'shows',
        list_filter='public_lists',
        add_delay=add_delay,
        sort=sort,
        no_search=no_search,
        notifications=notifications,
        ignore_blacklist=ignore_blacklist
    )


def automatic_movies_public_lists(
        add_delay=2.5,
        sort='votes',
        no_search=False,
        notifications=False,
        ignore_blacklist=False,
        rotten_tomatoes=None,
):
    return _automatic_media(
        'movies',
        list_filter='public_lists',
        add_delay=add_delay,
        sort=sort,
        no_search=no_search,
        notifications=notifications,
        ignore_blacklist=ignore_blacklist,
        rotten_tomatoes=rotten_tomatoes
    )


def automatic_shows_user_lists(
        add_delay=2.5,
        sort='votes',
        no_search=False,
        notifications=False,
        ignore_blacklist=False,
):
    return _automatic_media(
        'shows',
        list_filter='user_lists',
        add_delay=add_delay,
        sort=sort,
        no_search=no_search,
        notifications=notifications,
        ignore_blacklist=ignore_blacklist
    )


def automatic_movies_user_lists(
        add_delay=2.5,
        sort='votes',
        no_search=False,
        notifications=False,
        ignore_blacklist=False,
        rotten_tomatoes=None,
):
    return _automatic_media(
        'movies',
        list_filter='user_lists',
        add_delay=add_delay,
        sort=sort,
        no_search=no_search,
        notifications=notifications,
        ignore_blacklist=ignore_blacklist,
        rotten_tomatoes=rotten_tomatoes
    )


def _automatic_media(
        media_type,
        list_filter=None,
        add_delay=2.5,
        sort='votes',
        no_search=False,
        notifications=False,
        ignore_blacklist=False,
        rotten_tomatoes=None,
):
    """
    Common function for automatic adding of shows and movies.
    
    Args:
        media_type: 'shows' or 'movies'
        list_filter: 'public_lists', 'user_lists', or None for all lists
        add_delay: Seconds between each add request
        sort: Sort method for lists
        no_search: Disable search when adding
        notifications: Send notifications
        ignore_blacklist: Ignore blacklist filters
        rotten_tomatoes: Minimum RT score (movies only)
    """
    from media.trakt import Trakt

    # Configure based on media type
    if media_type == 'shows':
        config_key = 'shows'
        filters_config = cfg.filters.shows
        media_name_singular = 'show'
        media_name_plural = 'shows'
        target_service = 'Sonarr'
        callback_kwargs = {}
    elif media_type == 'movies':
        config_key = 'movies'
        filters_config = cfg.filters.movies
        media_name_singular = 'movie'
        media_name_plural = 'movies'
        target_service = 'Radarr'
        callback_kwargs = {'rotten_tomatoes': rotten_tomatoes} if rotten_tomatoes else {}
    else:
        raise ValueError(f"Invalid media_type: {media_type}. Must be 'shows' or 'movies'")

    total_added = 0
    # noinspection PyBroadException
    try:
        log.info("Automatic %s task started.", media_name_plural.title())

        # send notification
        if notifications and cfg.notifications.verbose:
            notify.send(message=f"Automatic {media_name_plural.title()} task started.")

        automatic_config = getattr(cfg.automatic, config_key)
        
        for list_type, value in automatic_config.items():
            added_items = None

            if list_type.lower() in ['interval', 'intervals']:
                continue

            # Apply list filtering if specified
            if list_filter == 'public_lists':
                # Only process public lists (non-user lists)
                if not (list_type.lower() in Trakt.non_user_lists or (
                        '_' in list_type and list_type.lower().partition("_")[0] in Trakt.non_user_lists)):
                    continue
            elif list_filter == 'user_lists':
                # Only process user lists (watchlist and custom lists)
                if list_type.lower() in Trakt.non_user_lists or (
                        '_' in list_type and list_type.lower().partition("_")[0] in Trakt.non_user_lists):
                    continue

            if list_type.lower() in Trakt.non_user_lists or (
                    '_' in list_type and list_type.lower().partition("_")[0] in Trakt.non_user_lists):
                limit = value

                if limit <= 0:
                    log.info("SKIPPED Trakt's '%s' %s list.", list_type.capitalize(), media_name_plural)
                    continue
                else:
                    log.info("ADDING %d %s from Trakt's '%s' list.", limit, media_name_singular + "(s)", list_type.capitalize())

                local_ignore_blacklist = ignore_blacklist

                if list_type.lower() in filters_config.disabled_for:
                    local_ignore_blacklist = True

                # run callback
                added_items = _process_media(
                    media_type=media_type,
                    list_type=list_type,
                    add_limit=limit,
                    add_delay=add_delay,
                    sort=sort,
                    no_search=no_search,
                    notifications=notifications,
                    ignore_blacklist=local_ignore_blacklist,
                    **callback_kwargs
                )

            elif list_type.lower() == 'watchlist':
                for authenticate_user, limit in value.items():
                    if limit <= 0:
                        log.info("SKIPPED Trakt user '%s''s '%s'", authenticate_user, list_type.capitalize())
                        continue
                    else:
                        log.info("ADDING %d %s from Trakt user '%s''s '%s'", limit, 
                                media_name_singular + "(s)", authenticate_user, list_type.capitalize())

                    local_ignore_blacklist = ignore_blacklist

                    if f"watchlist:{authenticate_user}" in filters_config.disabled_for:
                        local_ignore_blacklist = True

                    # run callback
                    added_items = _process_media(
                        media_type=media_type,
                        list_type=list_type,
                        add_limit=limit,
                        add_delay=add_delay,
                        sort=sort,
                        no_search=no_search,
                        notifications=notifications,
                        authenticate_user=authenticate_user,
                        ignore_blacklist=local_ignore_blacklist,
                        **callback_kwargs
                    )

            elif list_type.lower() == 'lists':

                if len(value.items()) == 0:
                    log.info("SKIPPED Trakt's '%s' %s list.", list_type.capitalize(), media_name_plural)
                    continue

                for list_, v in value.items():
                    if isinstance(v, dict):
                        authenticate_user = v['authenticate_user']
                        limit = v['limit']
                    else:
                        authenticate_user = None
                        limit = v

                    if limit <= 0:
                        log.info("SKIPPED Trakt's '%s' %s list.", list_, media_name_plural)
                        continue

                    local_ignore_blacklist = ignore_blacklist

                    if f"list:{list_}" in filters_config.disabled_for:
                        local_ignore_blacklist = True

                    # run callback
                    added_items = _process_media(
                        media_type=media_type,
                        list_type=list_,
                        add_limit=limit,
                        add_delay=add_delay,
                        sort=sort,
                        no_search=no_search,
                        notifications=notifications,
                        authenticate_user=authenticate_user,
                        ignore_blacklist=local_ignore_blacklist,
                        **callback_kwargs
                    )

            if added_items is None:
                if list_type.lower() != 'lists':
                    log.info("FAILED ADDING %s from Trakt's '%s' list.", media_name_plural, list_type.capitalize())
                time.sleep(10)
                continue
            total_added += added_items

            # sleep
            time.sleep(10)

        log.info("FINISHED: Added %d %s total to %s!", total_added, media_name_singular + "(s)", target_service)
        # send notification
        if notifications and (cfg.notifications.verbose or total_added > 0):
            notify.send(message=f"Added {total_added} {media_name_singular}(s) total to {target_service}!")

    except Exception:
        log.exception("Exception while automatically adding %s: ", media_name_plural)
    return total_added


def run_automatic_mode(
        add_delay=2.5,
        sort='votes',
        no_search=False,
        run_now=False,
        no_notifications=False,
        ignore_blacklist=False,
):
    """Run Traktarr in automatic mode with separate intervals for public and user lists."""

    log.info("Automatic mode is now running.")

    # send notification
    if not no_notifications and cfg.notifications.verbose:
        notify.send(message="Automatic mode is now running with separate intervals for public lists and user lists.")

    # Add tasks to schedule and do first run if enabled
    scheduled_tasks = []

    # Helper function to get interval configuration
    def get_interval(media_type, list_type):
        media_config = getattr(cfg.automatic, media_type)
        # Use the new intervals configuration
        if hasattr(media_config, 'intervals') and media_config.intervals:
            if list_type in media_config.intervals:
                return media_config.intervals[list_type]
        return 0  # No interval configured

    # Helper function to schedule a task
    def schedule_task(media_type, list_type, interval, func):
        if interval and interval > 0:
            task_name = f"{media_type} {list_type.replace('_', ' ')}"
            log.info("Scheduled %s every %s hours", task_name, interval)
            
            # Build arguments based on media type
            args = [add_delay, sort, no_search, not no_notifications, ignore_blacklist]
            if media_type == 'movies':
                args.append(int(cfg.filters.movies.rotten_tomatoes) if cfg.filters.movies.rotten_tomatoes != "" else None)
            
            # Create and store the scheduled task
            task = schedule.every(interval).hours.do(func, *args)
            task.tag = task_name  # Add a tag for identification
            scheduled_tasks.append(task)
            
            if run_now:
                log.info("Running %s immediately", task_name)
                task.run()
                time.sleep(add_delay)
            
            return task
        return None

    # Schedule all tasks
    schedule_task('movies', 'public_lists', get_interval('movies', 'public_lists'), automatic_movies_public_lists)
    schedule_task('movies', 'user_lists', get_interval('movies', 'user_lists'), automatic_movies_user_lists)
    schedule_task('shows', 'public_lists', get_interval('shows', 'public_lists'), automatic_shows_public_lists)
    schedule_task('shows', 'user_lists', get_interval('shows', 'user_lists'), automatic_shows_user_lists)

    # Log if no tasks were scheduled
    if not scheduled_tasks:
        log.warning("No automatic tasks scheduled! Check your intervals configuration.")
    else:
        log.info("Successfully scheduled %d automatic tasks", len(scheduled_tasks))
        log.info("Initial schedule:")
        for task in scheduled_tasks:
            task_name = getattr(task, 'tag', 'Unknown task')
            next_run = task.next_run
            if next_run:
                log.info("  - %s: next run at %s", task_name, next_run.strftime('%Y-%m-%d %H:%M:%S'))

    # Enter running schedule
    last_schedule_log = 0
    schedule_log_interval = 3600  # Log schedule every hour
    
    while True:
        try:
            current_time = time.time()
            
            # Log next run time for each scheduled task (periodically)
            if current_time - last_schedule_log >= schedule_log_interval:
                if scheduled_tasks:
                    log.info("Current schedule status:")
                    for task in scheduled_tasks:
                        task_name = getattr(task, 'tag', 'Unknown task')
                        next_run = task.next_run
                        if next_run:
                            log.info("  - %s: next run at %s", task_name, next_run.strftime('%Y-%m-%d %H:%M:%S'))
                        else:
                            log.info("  - %s: no next run scheduled", task_name)
                else:
                    log.info("No tasks scheduled")
                last_schedule_log = current_time
            
            # Sleep until next run
            idle_seconds = schedule.idle_seconds()
            if idle_seconds > 0:
                next_run_time = schedule.next_run()
                if next_run_time:
                    log.debug("Next job at %s (sleeping %d seconds)", next_run_time.strftime('%Y-%m-%d %H:%M:%S'), idle_seconds)
                time.sleep(idle_seconds)
            else:
                time.sleep(1)  # Brief pause if no idle time
                
            # Check jobs to run
            schedule.run_pending()

        except Exception as e:
            log.exception("Unhandled exception occurred while processing scheduled tasks: %s", e)
            time.sleep(1)


############################################################
# MISC
############################################################

def init_notifications():
    # noinspection PyBroadException
    try:
        for notification_name, notification_config in cfg.notifications.items():
            if notification_name.lower() == 'verbose':
                continue

            notify.load(**notification_config)
    except Exception:
        log.exception("Exception initializing notification agents: ")
    return


# Handles exit signals, cancels jobs and exits cleanly
# noinspection PyUnusedLocal
def exit_handler(signum, frame):
    log.info("Received %s, canceling jobs and exiting.", signal.Signals(signum).name)
    schedule.clear()
    exit()
