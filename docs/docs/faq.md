
How can I access a data file in my package?
-------------------------------------------

When your agent is submitted, it is run in an environment different from that in which the tournament
will be run. This means that you **cannot** use hardcoded paths in your agent. Moreover, you (and we) do
not know in advance what will be the current directory when the tournament is run. For this reason, it is
**required** that if you access any files in your agent, you should use a path relative to the file in which
the code accessing these files is located. Please note that accessing ANY FILES outside the directory of
your agent is **prohibited** and **will lead to immediate disqualification** for obvious security reasons.
There are no second chances in this one.

Let's assume that your file structure is something like that:

    base
    ├── sub
    │   ├── myagent.py
    │   └── otherfiles.py
    ├── data
    │   └── myfile.csv
    └── tests


Now you want to access the file *myfile.csv* when you are inside *myagent.py*. To do so you can use the following code::

    import pathlib
    path_2_myfile = pathlib.Path(__file__).parent.parent / "data" / "myfile.csv"

Can my agent pass data to my other agents between negotiations?
---------------------------------------------------------------
**NO** Passing data to your agents between negotiations will lead to disqualification.

Can my agent read data from the HDD outside my agent's folder?
--------------------------------------------------------------
**NO** Your agent can only read files that you submitted to us in your zip file.
It cannot modify these files in anyway during the competition.
It cannot read from anywhere else in secondary storage. Trying to do
so will lead to disqualification.

Can my agent write data to the HDD during the negotiation?
---------------------------------------------------------
**NO** The agent is not allowed to write anything to the hard disk during the
competition.

Can I print to the screen to debug my agent?
--------------------------------------------
**PLEASE DO NOT**

Printing to the screen in your agent will prevent us from monitoring the progress of tournament
runs and will slow down the process. Moreover, it is not useful anyway because the tournaments are run in
parallel.

If you really need to print something (e.g. for debugging purposes), please remove all print
statements before submission. We will never touch your code after submission so we cannot remove them.


Can I write arbitrary code in my module besides the negotiator class definition?
--------------------------------------------------------------------------------
When python imports your module, it runs everything in it so the top level code should be only one of these:

    - Class definitions
    - Function definitions
    - Variable definitions
    - Arbitrary code that runs in few milliseconds and prints nothing

Any other code *must* be protected inside::

    if __name__ == "__main__"

For example, if you want to run a simulation to test your agent. *DO NOT USE SOMETHING LIKE THIS*::

    anl2024_tournament(....)

But something like this::

    def main():
        anl2024_tournament(....)

    if __name__ == "__main__":
        main()

This way, importing your module will not run the world simulation.

I ran a simulation using "anl tournament2024" command. Where are my log files?
------------------------------------------------------------------------

If you did not pass "--no-log", you will find the log files
at *~/negmas/anl2024/[date-time-uuid]*


I implement my agent using multiple files. How should I import them?
--------------------------------------------------------------------

Assume that you have the following file structure

    base
    ├── subfolder
    │   └── component2.py
    ├── component1.py
    └── agent.py

In your `agent.py` file, you want to import your other files::

    import component1
    import subfolder.component2

This will **not** work because in the actual competition `component1.py` and
`component2.py` will not be in python path.

There are two ways to solve it:

The clean way is to use relative imports. You will need to turn your agent int a package
by adding empty `__init__.py` files to every folder you want to import from::

    base
    ├── sub
    │   ├── __init__.py
    │   └── component2.py
    ├── __init__.py
    ├── component1.py
    └── agent.py

You can now change your import to::

    import .component1
    import .subfolder.component2

Notice the extra dot (`.`)

Another way that does not require any modification of your file structure is to add the following lines
**before** your imports::

    import os, sys
    sys.path.append(os.path.dirname(__file__))

Note that the later method has the disadvantage of putting your components at the **end** of the path which
means that if you have any classes, functions, etc with a name that is defined in *any* module that appears
earlier in the path, yours will be hidden.
