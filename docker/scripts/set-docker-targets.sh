#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Command line args: $@${NC}"

ORIGINAL_COMMAND="$@"







if [ -n "$ENV" ]; then
	ENV_VALUE=$ENV
	echo -e "${GREEN}Using ENV=$ENV_VALUE from environment variable${NC}"
elif [[ "$1" == ENV=* ]]; then

	ENV_VALUE=${1#ENV=}

	shift
	echo -e "${GREEN}Detected ENV=$ENV_VALUE from command line argument${NC}"
else

	if [ -f .env ]; then

		ENV_FROM_FILE=$(grep "^ENV=" .env | cut -d= -f2)
		if [ -n "$ENV_FROM_FILE" ]; then
			ENV_VALUE=$ENV_FROM_FILE
			echo -e "${GREEN}Using ENV=$ENV_VALUE from .env file${NC}"
		else

			ENV_VALUE=1
			echo -e "${YELLOW}ENV not found in .env file, defaulting to ENV=$ENV_VALUE${NC}"
		fi
	else

		ENV_VALUE=1
		echo -e "${YELLOW}No .env file found, defaulting to ENV=$ENV_VALUE${NC}"
	fi
fi

if [[ "$ORIGINAL_COMMAND" == *"build kolct_backend"* || "$ORIGINAL_COMMAND" == *"build kolct_celery_worker"* ]]; then

	if [ "$ENV_VALUE" = "1" ]; then
		DOCKER_TARGET="development"
	else
		DOCKER_TARGET="production"
	fi

	echo -e "${GREEN}Setting Docker target to: $DOCKER_TARGET for kolct_backend/kolct_celery components${NC}"
	DOCKER_TARGET=$DOCKER_TARGET "$@"
elif [[ "$ORIGINAL_COMMAND" == *"build frontend"* || "$ORIGINAL_COMMAND" == *"build storybook"* ]]; then

	if [ "$ENV_VALUE" = "1" ]; then
		DOCKER_TARGET="builder"
	else
		DOCKER_TARGET="production"
	fi

	echo -e "${GREEN}Setting Docker target to: $DOCKER_TARGET for frontend/storybook components${NC}"
	DOCKER_TARGET=$DOCKER_TARGET "$@"
else

	if [ "$ENV_VALUE" = "1" ]; then

		export BACKEND_TARGET=development
		export FRONTEND_TARGET=builder
	else
		export BACKEND_TARGET=production
		export FRONTEND_TARGET=production
	fi
	

	export PROJECT_NAME=${PROJECT_NAME:-kolct}

	echo -e "${GREEN}Using multiple targets:${NC}"
	echo -e "  ${BLUE}BACKEND_TARGET=${GREEN}$BACKEND_TARGET${NC}"
	echo -e "  ${BLUE}FRONTEND_TARGET=${GREEN}$FRONTEND_TARGET${NC}"

	if [[ "$ORIGINAL_COMMAND" == *"docker-compose.gpu.yml"* || "$ORIGINAL_COMMAND" == *"docker-compose.mac-gpu.yml"* ]]; then
		echo -e "${GREEN}GPU acceleration enabled${NC}"
	fi

	env BACKEND_TARGET=$BACKEND_TARGET FRONTEND_TARGET=$FRONTEND_TARGET PROJECT_NAME=$PROJECT_NAME "$@"
	exit $?
fi
