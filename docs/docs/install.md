# Preparing Development Environment

## Direct (Recommended)

### Creating and activating a virtual environment
As always recommended, you should create a virtual environment for your development. You can use your IDE to do that or simply run the following command:
```bash
python -m venv .venv
```
You should always activate your virtual environment using:

=== windows
```bash
.venv\Scripts\activate.bat
```
=== Linux/MacOS
```bash
source .venv/bin/activate
```

### Installing the ANL package
The second step is to install the `anl` package using:

```bash
python -m pip install anl
```

### Downloading the Skeleton

The next step is to download the template from [here](https://yasserfarouk.github.io/files/anl/anl.zip). Please familiarize yourself with the competition rules availabe at the [competition website](https://scml.cs.brown.edu/anl).
After downloading and uncompressing the template, you should do the following steps:

1. Modify the name of the single class in `myagent.py` (currently called `MyNegotiator`) to a representative name for your agent. We will use `AwsomeNegotiator` here. You should then implement your agent logic by modifying this class.
   - Remember to change the name of the agent in the last line of the file to match your new class name (`AwsomeNegotiator`).
   - Remember to update the `agent class` in the submission form on the  [competition website](https://scml.cs.brown.edu/anl) to `AwsomeNegotiator`.
2. Start developing your agent as will be explained later in the tutorial
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

You can visualize tournaments by running:

```bash
anlv show
```

## Using Docker

If you prefer not to install anything on your machine or if you cannot use python 3.11 or later, you can use docker for development as follows.


### Downloading the Skeleton

The first step is to download the template from [here](https://yasserfarouk.github.io/files/anl/anl.zip). Please familiarize yourself with the competition rules availabe at the [competition website](https://scml.cs.brown.edu/anl).
After downloading and uncompressing the template, you should do the following steps:

1. Modify the name of the single class in `myagent.py` (currently called `MyNegotiator`) to a representative name for your agent. We will use `AwsomeNegotiator` here. You should then implement your agent logic by modifying this class.
   - Remember to change the name of the agent in the last line of the file to match your new class name (`AwsomeNegotiator`).
   - Remember to update the `agent class` in the submission form on the  [competition website](https://scml.cs.brown.edu/anl) to `AwsomeNegotiator`.
2. Start developing your agent as will be explained later in the tutorial

### Build the image and container

Run the following command on the root folder of your template to create and prepare the image and container that will be used for development:

```bash
docker compose up --build
```

This will take several minutes. Once the images are ready, you can run ANL commands as in the direct development method but you need to prefix each command with one of the following:

=== windows
```bash
docker-run.bat
```

=== Linux/MacOS
```bash
docker-run.sh
```

Here are some examples on windows (replace docker-run.bat with docker-run.sh for Linux/MacOS):

3. You can use the following ways to test your agent:
    - Run the following command to test your agent from the root folder of the extracted skeleton:
      ```bash
      docker-run.bat python -m myagent.myagent
      ```
    - Use the `anl` command line utility from the root folder of the extracted skeleton:
      ```bash
      docker-run.bat anl tournament2024 --path=. --competitors="myagent.myagnet.AwsomeNegotiator;Boulware;Conceder"
      ```
      This method is more flexible as you can control all aspects of the tournament to run.
      Use `anl tournament2024 --help`  to see all available options.

    - You can directly call `anl2024_tournament()` passing your agent as one of the competitors. This is the most flexible method and will be used in the tutorial.

You can visualize tournaments by running:

```bash
docker-run.bat anlv show
```
