import argparse
from subprocess import run
import os
import pytest
from typing import Callable
import evolve 

#NOTE: This runs expecting to start in the BitstreamEvolution parent directory

@pytest.fixture
def evolve_arg_parse_function() -> Callable[[str],evolve.EvolveArgs]:
    return evolve.get_evolve_args_from_argument_string
    

def test_terminal_connects():
    """Verify that any failures are with the command running rather than our setup to run the command."""

    program = run("ls".split(" "),capture_output=True)
    assert program.returncode == 0
    assert program.stdout is not None

def test_evolve_runs_without_error():
    """Verify that evolve, running in --test mode does not error out, and writes to stdout"""

    program = run("python3 src/evolve.py --test".split(" "),capture_output=True)
    empty = [None,'',b'']
    # assert no errors, standard printout
    assert program.returncode == 0
    assert program.stderr in empty
    assert program.stdout not in empty

@pytest.mark.parametrize("flag",["-c","--config"])
@pytest.mark.parametrize("configName",["config.ini","config1.ini","thisIsAVeryLongConfigNameThatShouldWorkWellConfig.ini","conf_01.ini"])
def test_config_is_interpreted(flag:str,configName:str,evolve_arg_parse_function:Callable):
    "Tests the config is interpreted correctly"

    terminal_arguments = flag+" "+configName
    args:evolve.EvolveArgs = evolve_arg_parse_function(terminal_arguments)
    assert args.config == configName, "'"+terminal_arguments + "' was not valid"

