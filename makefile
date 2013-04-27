TARGET = pairs
SRC = pairs.cpp

all:
	@if [ -d data ]; then \
		g++ -o $(TARGET) $(SRC); \
		echo "gcc -o $(TARGET) $(SRC)"; \
	else \
		echo "Error! 'data' directory not found."; \
	fi


