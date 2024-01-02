# Preparing Development Environment

To participate in [ANL 2024](https://scml.cs.brown.edu/anl), you need to prepare a local development environment in your machine, download the [skeleton](https://yasserfarouk.github.io/files/anl/anl.zip), and start hacking. This section of the documentation describes **two** ways to do that.

## Direct (Recommended)

This is the recommended method. It requires you to use an installation of python $3.11$ or later on your machine.

### 0. Installing Python
If -- for some reason -- you do not have python installed in your machine, start by installing it from [python.org](https://www.python.org/downloads/). You can also use any other method to install python 3.11 or later.

### 1. Creating and activating a virtual environment

!!! info
    optional but **highly** recommended

As always recommended, you should create a virtual environment for your development. You can use your IDE to do that or simply run the following command:
```bash
python -m venv .venv
```
You should always activate your virtual environment using:

=== "Windows"

    ``` bat
    .venv\Scripts\activate.bat
    ```

=== "Linux/MacOS"

    ``` bash
    source .venv/bin/activate
    ```

Of course, you can use any other method for creating your virtual environment (e.g. [anaconda](https://www.anaconda.com), [hatch](https://github.com/pypa/hatch), [poetry](https://python-poetry.org), [pyenv](https://github.com/pyenv/pyenv), [virtualenv](https://virtualenv.pypa.io/en/latest/) or any similar method). Whatever method you use, it is highly recommended not to install packages (anl or otherwise) directly on your base python system.

### 2. Installing the ANL package
The second step is to install the `anl` package using:

```bash
python -m pip install anl
```

### 3. Development

The next step is to download the template from [here](https://yasserfarouk.github.io/files/anl/anl.zip). Please familiarize yourself with the competition rules availabe at the [competition website](https://scml.cs.brown.edu/anl).
After downloading and uncompressing the template, you should do the following steps:

1. Modify the name of the single class in `myagent.py` (currently called `MyNegotiator`) to a representative name for your agent. We will use `AwsomeNegotiator` here. You should then implement your agent logic by modifying this class.
    - Remember to change the name of the agent in the last line of the file to match your new class name (`AwsomeNegotiator`).
2. Start developing your agent as will be explained later in the [tutorial](https://yasserfarouk.github.io/anl/tutorials/tutorial/).
3. You can use the following ways to test your agent:
    - Run the following command to test your agent from the root folder of the extracted skeleton:
      ```bash
      python -m myagent.myagent
      ```
    - Use the `anl` command line utility from the root folder of the extracted skeleton:
      ```bash
      anl tournament2024 --path=. --competitors="myagent.myagnet.AwsomeNegotiator;Boulware;Conceder"
      ```
      This method is more flexible as you can control all aspects of the tournament to run.
      Use `anl tournament2024 --help`  to see all available options.

    - You can directly call `anl2024_tournament()` passing your agent as one of the competitors. This is the most flexible method and will be used in the tutorial.
    - You can visualize tournaments by running:

        ```bash
        anlv show
        ```

5. Submit your agent to the [official submission website](https://scml.cs.brown.edu/anl):
    - Remember to update the `Class Name` (`AwsomeNegotiator` in our case) and `Agent Module` (`myagent.myagent` in our case) in the submission form on the  [competition website](https://scml.cs.brown.edu/anl) to `AwsomeNegotiator`.
    - If you need any libraries that are not already provided by `anl`, please include them in the `Dependencies` in a semi-colon separated list when submitting your agent.


## Using Docker

!!! warning
    You only need this if you do not want (or cannot) install locally on your machine.

If you prefer not to install python and the anl package on your machine or if you cannot use python 3.11 or later, you can use docker for development as follows.

### 0. Installing Docker

Docker is a container system that allows you to run applications in separated containers within your machine. Please install it using the [official installation guide](https://docs.docker.com/engine/install/).

### 1. Build the image and container

Run the following command on the root folder of your template to create and prepare the image and container that will be used for development:

```bash
docker compose up --build
```

This will take several minutes first time. Once this initial step is done, you can start the container again without rebuilding it using:

```bash
docker compose up
```


### 2. Development

The first step is to download the template from [here](https://yasserfarouk.github.io/files/anl/anl.zip). Please familiarize yourself with the competition rules availabe at the [competition website](https://scml.cs.brown.edu/anl).
After downloading and uncompressing the template, you should do the following steps:

1. Modify the name of the single class in `myagent.py` (currently called `MyNegotiator`) to a representative name for your agent. We will use `AwsomeNegotiator` here. You should then implement your agent logic by modifying this class.
     - Remember to change the name of the agent in the last line of the file to match your new class name (`AwsomeNegotiator`).
     - Remember to update the `Class Name` (`AwsomeNegotiator` in our case) and `Agent Module` (`myagent.myagent` in our case) in the submission form on the  [competition website](https://scml.cs.brown.edu/anl) to `AwsomeNegotiator`.
     - If you need any libraries that are not already provided by `anl`, please include them in the `Dependencies` in a semi-colon separated list when submitting your agent.
2. Start developing your agent as will be explained later in the [tutorial](https://yasserfarouk.github.io/anl/tutorials/tutorial/). Any changes you do in the skeleton, will be reflected in the container.
3. You can use the following ways to test your agent:
      - Run the following command to test your agent from the root folder of the extracted skeleton:

        === "Windows"

            ```bash
            docker-run.bash python -m myagent.myagent
            ```

        === "Linux/MacOS"

            ```bash
            docker-run.sh python -m myagent.myagent
            ```

      - Use the `anl` command line utility from the root folder of the extracted skeleton:

        === "Windows"

            ```bash
            docker-run.bat anl tournament2024 --path=. --competitors="myagent.myagnet.AwsomeNegotiator;Boulware;Conceder"
            ```
        === "Linux/MacOS"

            ```bash
            docker-run.sh anl tournament2024 --path=. --competitors="myagent.myagnet.AwsomeNegotiator;Boulware;Conceder"
            ```

        This method is more flexible as you can control all aspects of the tournament to run.

      - You can directly call `anl2024_tournament()` passing your agent as one of the competitors. This is the most flexible method and will be used in the tutorial.

      - You can visualize tournaments by running:

        === "Windows"

            ```bash
            docker-run.bat anlv show
            ```
        === "Linux/MacOS"

            ```bash
            docker-run.sh anlv show
            ```

5. Submit your agent to the [official submission website](https://scml.cs.brown.edu/anl):
     - Remember to update the `Class Name` (`AwsomeNegotiator` in our case) and `Agent Module` (`myagent.myagent` in our case) in the submission form on the  [competition website](https://scml.cs.brown.edu/anl) to `AwsomeNegotiator`.
     - If you need any libraries that are not already provided by `anl`, please include them in the `Dependencies` in a semi-colon separated list when submitting your agent.

### 3. Clear the container

When you finish your development, you can stop the containers used by this docker network using:

```bash
docker compose down
```

