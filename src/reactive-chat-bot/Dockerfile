# Use a base Python 3.13 image
FROM --platform=linux/amd64 python:3.13-slim-bookworm

# Create a non-root user
RUN useradd -ms /bin/bash appuser

# Create .streamlit folder and fix permissions
RUN mkdir -p /.streamlit \
    && chown -R appuser:appuser /.streamlit

RUN mkdir -p /app \
    && chown -R appuser:appuser /app

COPY ./app/.streamlit /.streamlit/.
# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app .

# Switch to non-root user
USER appuser

# Expose the port your Streamlit app will run on
EXPOSE 8501

# Command to run your Streamlit application
CMD ["streamlit", "run", "protected_bot.py"]
