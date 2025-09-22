RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

COMPOSE_FILE="docker/docker-compose.yml"
OS_TYPE=$(uname -s)
ARCH_TYPE=$(uname -m)

if [ "$OS_TYPE" = "Darwin" ] && [ "$ARCH_TYPE" = "arm64" ]; then
	echo -e "${GREEN}✅ Detected Mac with Apple Silicon (M1/M2)${NC}"
	COMPOSE_GPU_FILE="docker/docker-compose.mac-gpu.yml"

	echo "Starting with Apple Silicon GPU acceleration..."
	echo "This will use Metal for GPU acceleration if available."

	GPU_TYPE="Apple Silicon (Metal)"

elif [ "$OS_TYPE" = "Darwin" ]; then
	echo -e "${YELLOW}⚠️ Detected Mac with Intel processor${NC}"
	COMPOSE_GPU_FILE="docker/docker-compose.mac-gpu.yml"

	echo "Starting with limited GPU support..."
	echo "Note: Intel Macs have limited GPU acceleration capabilities with Docker."

	GPU_TYPE="Intel integrated (limited support)"

else

	echo "Checking for NVIDIA GPU support..."
	if ! command -v nvidia-smi &>/dev/null; then
		echo -e "${RED}❌ NVIDIA drivers not found. Please install NVIDIA drivers first.${NC}"
		exit 1
	fi

	echo -e "${GREEN}✅ NVIDIA drivers detected${NC}"
	nvidia-smi

	if ! docker info &>/dev/null; then
		echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
		exit 1
	fi

	if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &>/dev/null; then
		echo -e "${RED}❌ NVIDIA Docker runtime test failed. Please install nvidia-docker2 properly.${NC}"
		echo "See docs/ollama-gpu-setup.md for installation instructions."
		exit 1
	fi

	echo -e "${GREEN}✅ NVIDIA Docker runtime is configured properly${NC}"
	COMPOSE_GPU_FILE="docker/docker-compose.gpu.yml"
	GPU_TYPE="NVIDIA CUDA"
fi

echo -e "${GREEN}✅ Docker is running${NC}"

echo "🚀 Starting application with GPU support for Ollama using $GPU_TYPE..."

ENV=1 ./docker/scripts/set-docker-targets.sh docker compose -f $COMPOSE_FILE -f $COMPOSE_GPU_FILE up -d

echo "⏳ Waiting for Ollama to start..."
sleep 10

if curl -s http://localhost:11434/api/tags | grep -q ""; then
	echo -e "${GREEN}✅ Ollama is running!${NC}"

	if curl -s http://localhost:11434/api/gpu 2>/dev/null | grep -q "gpus"; then
		echo "GPU Information:"
		curl -s http://localhost:11434/api/gpu | grep -v "^$" || echo "No detailed GPU information available"
	else
		echo "Ollama is running with $GPU_TYPE."
		echo "Note: Detailed GPU information may not be available on all platforms."
	fi
else
	echo -e "${YELLOW}⚠️ Ollama may not be running correctly.${NC}"
	echo "Please check the logs for more information:"
	echo "docker logs kolct_ollama"
fi

echo "🌐 WebUI available at: http://localhost:${WEBUI_PORT:-3031}"
echo "📊 Backend API available at: http://localhost:${API_PORT:-8000}"
echo "🔍 Frontend available at: http://localhost:${FRONTEND_PORT:-5173}"
