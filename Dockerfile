FROM python:3.9-slim-bullseye

# 1. Install system dependencies (including a C compiler)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       build-essential \
       git \
       sqlite3 \
       libsqlite3-dev \
       # you may also need others like
       # libffi-dev libssl-dev for certain packages
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Set an environment variable (default value assigned)
ENV OPENAI_API_KEY=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
ENV EPINECONE_API_KEY=pcsk_3qSVug_KXkWjzaKNehQ9mycSsUaz2HnjVLGDH2DrdgQJykxGQp4FBTwby5VDkPPf7LWnFi
ENV ANTHROPIC_API_KEY=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
ENV MONGO_CONNECTION_STRING=mongodb+srv://shivam:Shivam%40123@autodoc.an3p0.mongodb.net/

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the FastAPI port (e.g., 8000)
EXPOSE 8000

# Run the FastAPI app with Uvicorn
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
