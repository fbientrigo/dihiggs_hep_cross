.PHONY: test clean

test:
	python3 -m pytest

clean:
	rm -rf outputs .pytest_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
