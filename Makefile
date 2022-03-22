.PHONY: test, lint, typecheck
test:
	pytest
lint:
	flake8
typecheck:
	mypy
formatcheck:
	black --check .

# Alias
.PHONY: tests
tests:
	make -s test

.PHONY: qa
qa:
	make -s formatcheck
	make -s lint
	make -s typecheck
	make -s test
