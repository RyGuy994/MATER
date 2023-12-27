DEV_FILE = dev-docker-compose.yml
DEV_DOCKER_COMPOSE=docker-compose -f $(DEV_FILE)
default: build

#=========================================================#
# Builds and does other docker functionality for Mater #
#=========================================================#
build:
	@echo "Building MATER!"
	@$(DEV_DOCKER_COMPOSE) up --build
up:
	@echo "Getting Mater up!"
	@$(DEV_DOCKER_COMPOSE) up
clean: # Removes all orphans processes
	@echo "Cleaning up processes for Mater!"
	@$(DEV_DOCKER_COMPOSE) down -v
stop:
	@echo "Shutting MATER down now!"
	@$(DEV_DOCKER_COMPOSE) down 
detached-pg: # Runs the containers in daemon mode
	@echo "Running MATER in detached mode!"
	@$(DEV_DOCKER_COMPOSE) up -d --build