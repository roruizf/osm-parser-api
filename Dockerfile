# Start from a Python base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install git so we can clone the toolkit repository
# Also clean up apt cache to keep image size down
RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Clone the OpenStudio-Toolkit repository from GitHub into the /app directory
# It will initially be cloned as 'OpenStudio-Toolkit' (with hyphen)
# Then, rename it to 'OpenStudio_Toolkit' (with underscore)
RUN git clone https://github.com/roruizf/OpenStudio-Toolkit.git OpenStudio-Toolkit-temp && \
    mv OpenStudio-Toolkit-temp OpenStudio_Toolkit

# Now, OpenStudio_Toolkit (with underscore) should exist in /app/OpenStudio_Toolkit

# Copy the requirements file from your GitHub repo (the build context)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your main application file from your GitHub repo
COPY main.py .

# Expose the port the app runs on (Hugging Face Spaces typically uses 7860)
EXPOSE 7860

# Command to run the Uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]