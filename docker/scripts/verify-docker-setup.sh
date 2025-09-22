RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo "=== Docker Setup Verification ==="
echo ""

if ! command -v docker &>/dev/null; then
	echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
	exit 1
else
	echo -e "${GREEN}✅ Docker is installed.${NC}"
fi

if ! docker info &>/dev/null; then
	echo -e "${RED}❌ Docker daemon is not running. Please start Docker.${NC}"
	exit 1
else
	echo -e "${GREEN}✅ Docker daemon is running.${NC}"
fi

if ! command -v docker compose &>/dev/null; then
	echo -e "${YELLOW}⚠️ Docker Compose V2 (docker compose) is not available. We recommend using Docker Compose V2.${NC}"

	if ! command -v docker-compose &>/dev/null; then
		echo -e "${RED}❌ Docker Compose V1 (docker-compose) is also not available.${NC}"
		exit 1
	else
		echo -e "${YELLOW}⚠️ Using Docker Compose V1 (docker-compose). Consider upgrading to Docker Compose V2.${NC}"
	fi
else
	echo -e "${GREEN}✅ Docker Compose V2 is installed.${NC}"
fi

if [ ! -f "docker/docker-compose.yml" ]; then
	echo -e "${RED}❌ docker/docker-compose.yml not found.${NC}"
	exit 1
else
	echo -e "${GREEN}✅ docker/docker-compose.yml exists.${NC}"
fi

if [ ! -f "docker/docker-compose.gpu.yml" ]; then
	echo -e "${YELLOW}⚠️ docker/docker-compose.gpu.yml not found. GPU support will not be available.${NC}"
else
	echo -e "${GREEN}✅ docker/docker-compose.gpu.yml exists.${NC}"
fi

if [ ! -f "docker/docker-compose.prod.yml" ]; then
	echo -e "${YELLOW}⚠️ docker/docker-compose.prod.yml not found. Production configuration will not be available.${NC}"
else
	echo -e "${GREEN}✅ docker/docker-compose.prod.yml exists.${NC}"
fi

if [ ! -f ".env" ]; then
	echo -e "${YELLOW}⚠️ .env not found. Creating a default one...${NC}"
	echo "# Environment type (1 for development, 0 for production)" >.env
	echo "ENV=1" >>.env
	echo "" >>.env
	echo "# Database settings" >>.env
	echo "DATABASE_NAME=mydatabase" >>.env
	echo "DATABASE_USER=postgres" >>.env
	echo "DATABASE_PASSWORD=postgres" >>.env
	echo "DATABASE_PORT=5432" >>.env
	echo "API_PORT=8000" >>.env
	echo "FRONTEND_PORT=5173" >>.env
	echo "REDIS_PORT=6379" >>.env
	echo "ADMIN_EMAIL=admin@example.com" >>.env
	echo "ADMIN_PASSWORD=admin" >>.env
	echo "" >>.env
	echo "# Development-specific settings" >>.env
	echo "DEV_ALLOWED_HOSTS=localhost,127.0.0.1" >>.env
	echo "DEV_CSRF_TRUSTED_ORIGINS=http://localhost:8009,http://127.0.0.1:8009,http://localhost:8747" >>.env
	echo "" >>.env
	echo "# Production-specific settings - UPDATE THESE BEFORE DEPLOYING" >>.env
	echo "PROD_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com" >>.env
	echo "PROD_CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com" >>.env
else
	echo -e "${GREEN}✅ .env exists.${NC}"
fi

OS_TYPE=$(uname -s)
ARCH_TYPE=$(uname -m)

if [ "$OS_TYPE" = "Darwin" ] && [ "$ARCH_TYPE" = "arm64" ]; then
	echo -e "${GREEN}✅ Mac with Apple Silicon (M1/M2) detected.${NC}"

	if [ ! -f "docker/docker-compose.mac-gpu.yml" ]; then
		echo -e "${YELLOW}⚠️ docker/docker-compose.mac-gpu.yml not found. Creating it...${NC}"
		cat >docker/docker-compose.mac-gpu.yml <<'EOF'
version: '3.8'

services:
  kolct_ollama:
    
    environment:
      - OLLAMA_HOST=0.0.0.0
      
      - OLLAMA_USE_METAL=true

  
  kolct_backend:
    environment:
      - OLLAMA_GPU_ENABLED=true
      - OLLAMA_USE_METAL=true
    mem_limit: 8g
    cpus: 4.0

  
  kolct_ollama_webui:
    environment:
      - OLLAMA_GPU_ENABLED=true
      - OLLAMA_USE_METAL=true
EOF
		echo -e "${GREEN}✅ Created docker/docker-compose.mac-gpu.yml for Apple Silicon support${NC}"
	else
		echo -e "${GREEN}✅ docker/docker-compose.mac-gpu.yml exists${NC}"
	fi

	echo -e "${GREEN}✅ Metal GPU acceleration should be available for Ollama${NC}"

elif [ "$OS_TYPE" = "Darwin" ]; then
	echo -e "${YELLOW}⚠️ Mac with Intel processor detected. Limited GPU support available.${NC}"

	if [ ! -f "docker/docker-compose.mac-gpu.yml" ]; then
		echo -e "${YELLOW}⚠️ docker/docker-compose.mac-gpu.yml not found. Creating it...${NC}"
		cat >docker/docker-compose.mac-gpu.yml <<'EOF'
version: '3.8'

services:
  kolct_ollama:
    
    environment:
      - OLLAMA_HOST=0.0.0.0

  
  kolct_backend:
    environment:
      - OLLAMA_GPU_ENABLED=false
    mem_limit: 8g
    cpus: 4.0

  
  kolct_ollama_webui:
    environment:
      - OLLAMA_GPU_ENABLED=false
EOF
		echo -e "${GREEN}✅ Created docker/docker-compose.mac-gpu.yml for Intel Mac${NC}"
	else
		echo -e "${GREEN}✅ docker/docker-compose.mac-gpu.yml exists${NC}"
	fi

	echo -e "${YELLOW}⚠️ Note: Intel Macs have limited GPU acceleration in Docker${NC}"

elif command -v nvidia-smi &>/dev/null; then
	echo -e "${GREEN}✅ NVIDIA drivers detected.${NC}"

	if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &>/dev/null; then
		echo -e "${GREEN}✅ NVIDIA Docker runtime is working.${NC}"
	else
		echo -e "${YELLOW}⚠️ NVIDIA Docker runtime test failed. GPU acceleration may not work correctly.${NC}"
		echo "   See docs/ollama-gpu-setup.md for instructions on setting up NVIDIA Docker runtime."
	fi

	if [ ! -f "docker/docker-compose.gpu.yml" ]; then
		echo -e "${YELLOW}⚠️ docker/docker-compose.gpu.yml not found.${NC}"
	else
		echo -e "${GREEN}✅ docker/docker-compose.gpu.yml exists${NC}"
	fi
else
	echo -e "${YELLOW}⚠️ No GPU support detected. Ollama will run on CPU only.${NC}"
fi

echo ""
echo "=== Verification Complete ==="
echo ""
echo "To start the application, run:"
echo -e "${GREEN}make up${NC}"
echo ""
echo "For GPU-accelerated Ollama, run:"
echo -e "${GREEN}make up-gpu${NC}"
echo ""
