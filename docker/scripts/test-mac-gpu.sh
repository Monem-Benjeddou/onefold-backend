RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

if [ "$(uname)" != "Darwin" ]; then
	echo -e "${RED}This script is for Mac only!${NC}"
	exit 1
fi

echo "=== Testing Mac GPU Acceleration ==="
echo ""

if ! docker info &>/dev/null; then
	echo -e "${RED}❌ Docker is not running. Please start Docker Desktop first.${NC}"
	exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

if ! docker ps | grep -q "kolct_ollama"; then
	echo -e "${YELLOW}⚠️ Ollama container is not running.${NC}"
	echo "Would you like to start it with GPU support? (y/n)"
	read -r answer
	if [[ "$answer" =~ ^[Yy]$ ]]; then
		echo "Starting Ollama with GPU support..."
		make up-gpu
	else
		echo "Exiting script. Please start Ollama with 'make up-gpu' first."
		exit 1
	fi
fi

echo -e "${GREEN}✅ Ollama container is running${NC}"

if docker exec -it kolct_ollama env | grep -q "OLLAMA_USE_METAL=true"; then
	echo -e "${GREEN}✅ OLLAMA_USE_METAL is enabled${NC}"
else
	echo -e "${YELLOW}⚠️ OLLAMA_USE_METAL environment variable is not set to true${NC}"
	echo "This may indicate Metal acceleration is not properly configured."
fi

ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
	echo -e "${GREEN}✅ Running on Apple Silicon ($ARCH)${NC}"
	HAS_METAL="likely"
else
	echo -e "${YELLOW}⚠️ Running on Intel Mac ($ARCH)${NC}"
	echo "Metal acceleration is limited on Intel Macs."
	HAS_METAL="unlikely"
fi

echo ""
echo "Would you like to test load a small model to check resource usage? (y/n)"
read -r answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
	echo "Loading a small model for testing (gemma:2b)..."
	echo "This may take a while if the model needs to be downloaded first."

	docker exec -it kolct_ollama pull gemma:2b

	echo "Testing model loading..."
	docker exec -it kolct_ollama ollama run gemma:2b "Write a one-sentence poem." &
	TEST_PID=$!

	echo "Monitoring resource usage (press Ctrl+C to stop)..."
	docker stats kolct_ollama --no-stream

	if ps -p $TEST_PID >/dev/null; then
		kill $TEST_PID 2>/dev/null
	fi

	if [ "$HAS_METAL" = "likely" ]; then
		echo -e "${GREEN}If you see high memory usage and GPU utilization, Metal acceleration is likely working.${NC}"
	else
		echo -e "${YELLOW}On Intel Macs, GPU acceleration will be limited, and CPU will do most of the work.${NC}"
	fi
fi

echo ""
echo "=== Test Complete ==="
echo ""
echo "For more information on GPU acceleration with Ollama, see:"
echo "docs/ollama-gpu-setup.md"
