DEV_FILE = docker-compose.override.yml
DEV_DOCKER_COMPOSE = docker-compose -f $(DEV_FILE)

WFE_DEV_FILE = dev-docker-compose.yml
WFE_DEV_DOCKER_COMPOSE = docker-compose -f $(WFE_DEV_FILE)

default: build

#=============================================================#
# Builds and does other docker functionality for MATER-WFE #
#=============================================================#
build:
	@echo "Building MATER-WFE!"
	@$(DEV_DOCKER_COMPOSE) up --build

up:
	@echo "Getting MATER-WFE up!"
	@$(DEV_DOCKER_COMPOSE) up

clean: # Removes all orphans processes
	@echo "Cleaning up processes for MATER-WFE!"
	@$(DEV_DOCKER_COMPOSE) down -v

stop:
	@echo "Shutting MATER-WFE down now!"
	@$(DEV_DOCKER_COMPOSE) down 

detached-pg: # Runs the containers in daemon mode
	@echo "Running MATER-WFE in detached mode!"
	@$(DEV_DOCKER_COMPOSE) up -d --build

test:
	@echo "Running MATER-WFE tests!"
	# Add your test commands here