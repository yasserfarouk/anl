Command Line Scripts
====================

When installing anl through the pip command, you get one command line tool that can be used to
aid your development and testing. This tool provides a unified interface to all anl commands.

The set of supported commands are:

===============       ===================================================================
 Command                                  Meaning
===============       ===================================================================
tournament2024        Runs a tournament with ANL 2024 settings
run2024               Runs a negotiation in ANL 2024 settings
version               Prints ANL version (and NegMAS version)
===============       ===================================================================


Arguments

========= ============================================
Argument   Meaning
========= ============================================
--help     Display a help screen
--gui      Runs the script as a GUI
========= ============================================

Running ANL 2024 Tournaments
----------------------------

Runs a tournament using ANL 2024 settings.  You can get help on this tool by running:

.. code-block:: console

    $ anl tournament2024 --help

These are the *optional* arguments of this tool:

========================================== ==============================================================
  Argument                                      Meaning
========================================== ==============================================================
  -n, --name TEXT                           The name of the tournament. The special
                                            value "random" will result in a random name
                                            [default: random]
  -s, --steps INTEGER                       Number of steps. If passed then --steps-min
                                            and --steps-max are ignored  [default: 10]
  --ttype, --tournament-type, --tournament  [collusion|std]
                                            The config to use. It can be collusion or
                                            std  [default: std]
  -t, --timeout INTEGER                     Timeout the whole tournament after the
                                            given number of seconds (0 for infinite)
                                            [default: -1]
  --configs INTEGER                         Number of unique configurations to
                                            generate.  [default: 5]
  --runs INTEGER                            Number of runs for each configuration
                                            [default: 2]
  --max-runs INTEGER                        Maximum total number of runs. Zero or
                                            negative numbers mean no limit  [default:
                                            -1]
  --competitors TEXT                        A semicolon (;) separated list of agent
                                            types to use for the competition. You can
                                            also pass the special value default for the
                                            default builtin agents  [default: Decentral
                                            izingAgent;BuyCheapSellExpensiveAgent;Rando
                                            mAgent]
  --non-competitors TEXT                    A semicolon (;) separated list of agent
                                            types to exist in the worlds as non-
                                            competitors (their scores will not be
                                            calculated).  [default: ]
  -l, --log DIRECTORY                       Default location to save logs (A folder
                                            will be created under it)  [default:
                                            ~/logs/tournaments]
  --world-config FILE                       A file to load extra configuration
                                            parameters for world simulations from.
  --verbosity INTEGER                       verbosity level (from 0 == silent to 1 ==
                                            world progress)  [default: 1]
  --log-ufuns / --no-ufun-logs              Log ufuns into their own CSV file. Only
                                            effective if --debug is given  [default:
                                            False]
  --log-negs / --no-neg-logs                Log all negotiations. Only effective if
                                            --debug is given  [default: False]
  --compact / --debug                       If True, effort is exerted to reduce the
                                            memory footprint whichincludes reducing
                                            logs dramatically.  [default: True]
  --raise-exceptions / --ignore-exceptions  Whether to ignore agent exceptions
                                            [default: True]
  --path TEXT                               A path to be added to PYTHONPATH in which
                                            all competitors are stored. You can path a
                                            : separated list of paths on linux/mac and
                                            a ; separated list in windows  [default: ]
  --cw INTEGER                              Number of competitors to run at every world
                                            simulation. It must either be left at
                                            default or be a number > 1 and < the number
                                            of competitors passed using --competitors
                                            [default: 3]
  --parallel / --serial                     Run a parallel/serial tournament on a
                                            single machine  [default: True]
  --config FILE                             Read configuration from FILE.
  --help                                    Show help message.
========================================== ==============================================================

Upon completion, a complete log and several statistics are saved in a new folder under the `log folder` location
specified by the `--log` argument (default is negmas/logs/tournaments under the HOME directory). To avoid over-writing
earlier results, a new folder will be created for each run named by the current date and time. The
folder will contain the following files:


