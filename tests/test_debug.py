"""
Debug test to understand CLI test failures
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, Mock
from click.testing import CliRunner
from cli.commands import app


def test_debug_movies_command():
    """Debug test to see what's happening with movies command."""
    runner = CliRunner()
    
    with patch('cli.commands.init_globals') as mock_init, \
         patch('cli.commands.add_multiple_movies') as mock_add_movies:
        
        result = runner.invoke(app, [
            'movies',
            '--list-type', 'trending',
            '--add-limit', '5',
            '--add-delay', '3.0',
            '--sort', 'release',
            '--rotten-tomatoes', '80',
            '--year', '2022',
            '--genres', 'action,thriller'
        ])
        
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        print(f"Exception: {result.exception}")
        
        print(f"init_globals called: {mock_init.called}")
        print(f"add_multiple_movies called: {mock_add_movies.called}")
        
        if result.exception:
            import traceback
            print("Traceback:")
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
        else:
            print("Command executed successfully!")
            
        # Try to see what arguments the movies function expects
        from cli.commands import movies
        import inspect
        sig = inspect.signature(movies.callback)
        print(f"Movies function signature: {sig}")
        print(f"Movies function parameters: {list(sig.parameters.keys())}")
        
        return result


if __name__ == "__main__":
    test_debug_movies_command()
