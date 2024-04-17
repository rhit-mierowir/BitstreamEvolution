"""
Generate a bash script to run multiple experiments.
Make sure you generate configs from base BitstreamEvolution Directory.

Origionally written by Allyn, improved and extended by Isaac.

"""

import os, stat
from typing import Generator, Any

# mkdir("data/SensitivityConfigs")

# Set some defaults
base_config_path =              "data/config.ini"
generated_configs_dir =         "data/GeneratedConfigs"
generated_bash_script_path =    "data/runGeneratedConfigs.sh"
results_output_directory =      "data/GeneratedConfigsResults"


# This will create the directory to put the generated configs in if it doesn't exist
if not os.path.isdir(generated_configs_dir):
    os.makedirs(generated_configs_dir)

#Make the directory for the final results
if not os.path.isdir(results_output_directory):
    os.makedirs(results_output_directory)



# All {variables_in_brackets} need to be specified and formatted later as .format(variables_in_brackets="value")
# It is fine to specify unused variables in .format(), but will error out if a value isn't included
# You only need to include the values here that you don't want to inherit from your base config.

######################### USEFUL CONFIG BASES ############################
sensitivity_config_base = \
"""[TOP-LEVEL PARAMETERS]
base_config = {base_config_path}

[FITNESS SENSITIVITY PARAMETERS]
test_circuit = data/saved_bests/{circuit_id}.asc
"""

# return the path to the new config
def sensitivity_config_generator()->Generator[str,None,None]:

    for circuit_id in range(10,510,10):

        config_path = os.path.join(generated_configs_dir, f"{circuit_id}.ini")
        # Create the config file using the config_base file
        with open(config_path, "w") as config_file:
            config_file.write(sensitivity_config_base.format(
                base_config_path = base_config_path,
                circuit_id = circuit_id
            ))

        yield config_path


pulse_count_config_base = \
"""[TOP-LEVEL PARAMETERS]
base_config = {base_config_path}

[FITNESS PARAMETERS]
fitness_func = {fitness_function}
desired_freq = {desired_frequency}

"""

def pulse_count_config_generator(target_pulses:list[int],
                use_tolerant_ff:bool=True,
                use_sensitive_ff:bool=True)->Generator[str,None,None]:
    """
    Generates configs for pulse_count experiments

    The order experiments will run if all fitness functions are selected is:
    tolerant -> sensitive

    Parameters
    ----------
    target_pulses : list[int]
        A list of all of the target pulse counts you want to train for
    use_tolerant_ff : bool, optional
        If each pulse get a run using the tolerant fitness function, by default True
    use_sensitive_ff: bool, optional
        If each pulse get a run using the sinsitive fitness function, by default True

    Yields
    ------
    Generator[str,None,None]
        The path to the output file generated.
    """
    def create_config(target_pulse_count:int,fitness_funciton:str)->str:
        # Generate the path for each pulse count
        config_path=os.path.join(generated_configs_dir,f"{target_pulse_count}_with__{fitness_funciton}.ini")

        with open(config_path, "w") as config_file:
            config_file.write(pulse_count_config_base.format(
                base_config_path = base_config_path,
                fitness_function = fitness_funciton,
                desired_frequency = target_pulse_count
            ))
        return config_path

    for target_pulse in target_pulses:
        if use_sensitive_ff:
            yield create_config(target_pulse,"SENSITIVE_PULSE_COUNT")
        if use_tolerant_ff:
            yield create_config(target_pulse,"TOLERANT_PULSE_COUNT")


def repeat(repeat_count:int, generator:Generator[Any,None,None])->Generator[Any,None,None]:
    """
    Repeats the outputs of the instantiated generator it is passed.

    Parameters
    ----------
    repeat_count : int
        number of times to duplicate the sequence
    generator : Generator[Any,None,None]
        Instantiated generator it duplicates

    Yields
    ------
    Generator[Any,None,None]
        The repeated output of the input generator
    """
    generator_results = list(generator)
    for i in range(repeat_count):
        for result in generator_results:
            yield result
        

## Select the config_generator you want to use and pass arguments
## OPTIONS:
# sensitivity_config_generator()
# pulse_count_config_generator(target_pulses = [1000,10000], use_tolerant_ff = True, use_sensitive_ff = True)
# repeat(2,pulse_count_config_generator(target_pulses = [1000, 10000], use_tolerant_ff = True, use_sensitive_ff = True))
config_generator = pulse_count_config_generator(target_pulses = [40000,20000,20000],use_tolerant_ff=False,use_sensitive_ff=True)

## Bash File Configuration

bash_head = \
"""#!/bin/bash
# make sure this was generated from the BitstreamEvolution folder at the base of this directory.

# This variables stores the number or errors that occour
ErrorCounter = 0
FailedCommands = ''


#Run Commands, log if they fail.
"""

evolve_command_base = "python3 src/evolve.py -c {config_path} -d {description} -o {output_directory}"

# The || only runs 2nd if left fails, && only if left succeeds
bash_command_wrapper_logic = \
"""{command}
   || ((ErrorCounter+=1)) && FailedCommands+=$'{command} \\n'

"""

bash_tail = \
"""
# Print out the results of the Tests
echo ""
echo "=================================== RESULTS ===================================="
echo ""
echo "Commands That Failed:"
echo "$FailedCommands"

echo "$ErrorCounter of {num_commands} commands Failed"
echo "The commands that failed are listed above."
"""

with open(generated_bash_script_path, 'w') as bash_file:
    # Invoke the bash shell for bash script
    bash_file.write(bash_head)

    command_count = 0
    for config_path in config_generator:

        # Add a call to this 
        bash_file.write(
            bash_command_wrapper_logic.format(
                command = evolve_command_base.format(
                    config_path = config_path,
                    description = f'"running config at: {config_path}"', 
                    # Note that it is important that outer string uses double quotes or this messes up wrapper logic
                    output_directory = results_output_directory
                )
            )
        )

        #count the number of commands we add
        command_count += 1
    
    bash_file.write(bash_tail.format(num_commands = command_count))

#ensure bash script is executable.
try:
    os.chmod(generated_bash_script_path,stat.S_IREAD
            |stat.S_IWRITE
            |stat.S_IRWXU
            |stat.S_IRWXG
            |stat.S_IRWXO)
except PermissionError:
    print(
    f"""
    You will need to make the bash file executable.
    Alternatively, you could run this command with sudo privilages. (sudo python3 ...)
    To do so run the following command:
    
    chmod +x {bash_file.name}

    """
    )

completion_message=\
f"""
--------------------------------------------------------------------------
Finished completing the bash file, and related folders.

Folder containing generated partial configs: {generated_configs_dir}
Reference base config: {base_config_path}
Results are output to the following directory: {results_output_directory}

Created the bash file at: {bash_file.name}
---------------------------------------------------------------------------

Begin the experiment by running ./{bash_file.name}

---------------------------------------------------------------------------
If you didn't run this script from the base of the BitstreamEvolution project,
it is best you regenerate the file after you cd there and run the file from that folder, too.

i.e.   .../BitstreamEvolution$ python3 src/tools/generate_configs.py
       .../BitstreamEvolution$ ./{bash_file.name}
"""

print(completion_message)