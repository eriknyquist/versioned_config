PYTHON := python3
TESTS_DIR := tests/

test:
	$(PYTHON) -m unittest discover -t $(TESTS_DIR) -s $(TESTS_DIR)
