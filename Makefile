.PHONY: build run stop

# Build the Docker image
build:
	docker-compose build

# Run the application
run:
	docker-compose up

# Stop the application
stop:
	docker-compose down

