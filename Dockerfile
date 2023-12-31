# Base image with Python 3.12
FROM python:3.12

# Working directory
WORKDIR /app

# Copy remaining project files
COPY . .

# Install dependencies
RUN pip install -U pip wheel
RUN pip install -e .
RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt
RUN pip install -r docs/requirements.txt

# expose anlv port
EXPOSE 8501
