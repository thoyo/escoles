.PHONY: build run stop

# Build the Docker image
build:
	docker-compose build

# Run the application
run:
	docker-compose up -d

# Stop the application
stop:
	docker-compose down

