FROM alpine:3.19

# Install bash, curl, Docker CLI (optional but recommended for compatibility with init-local.sh)
RUN apk add --no-cache bash curl docker-cli

WORKDIR /app

# Download and run the official init script
RUN curl -sSf https://raw.githubusercontent.com/quadratichq/quadratic-selfhost/main/init-local.sh -o init-local.sh \
    && chmod +x init-local.sh

# Expose necessary ports
EXPOSE 80 443 3001 3002 3003 4433 4455 8000

# Run the init script at container start, passing LICENSE_KEY as environment variable
CMD ["bash", "-i", "init-local.sh"]
