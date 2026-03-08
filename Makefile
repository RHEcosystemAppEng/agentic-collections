.PHONY: help install validate validate-skill-design validate-skill-design-changed generate serve clean test test-full check-uv

help:
	@echo "agentic-collections Documentation Generator"
	@echo ""
	@echo "Available targets:"
	@echo "  install                       - Install Python dependencies (requires uv)"
	@echo "  validate                      - Validate pack structure (plugin.json, .mcp.json, frontmatter)"
	@echo "  validate-skill-design         - Validate all skills (use PACK=rh-sre for a specific pack)"
	@echo "  validate-skill-design-changed - Validate only changed skills (staged + unstaged, for local dev)"
	@echo "  generate    - Generate docs/data.json"
	@echo "  serve       - Start local server on http://localhost:8000"
	@echo "  test        - Quick test (validate + generate + verify)"
	@echo "  test-full   - Full test suite (test + serve with browser open)"
	@echo "  clean       - Remove generated files"
	@echo "  update      - Full update (validate + generate)"
	@echo ""
	@echo "Requirements:"
	@echo "  uv - Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"

check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Error: uv is not installed"; \
		echo ""; \
		echo "Install uv with:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo ""; \
		echo "Or visit: https://github.com/astral-sh/uv"; \
		exit 1; \
	}

install: check-uv
	@echo "Installing Python dependencies with uv..."
	@uv sync
	@echo "Dependencies installed in isolated environment!"

validate: check-uv
	@echo "Validating agentic collection structure..."
	@uv run python scripts/validate_structure.py
	@echo "✓ Validation passed!"

validate-skill-design: check-uv
	@uv run python scripts/validate_skill_design.py $(if $(PACK),$(PACK))

validate-skill-design-changed: check-uv
	@VALIDATE_INCLUDE_UNCOMMITTED=1 ./scripts/ci-validate-changed-skills.sh

generate: check-uv
	@echo "Generating documentation..."
	@uv run python scripts/build_website.py
	@echo "✓ Documentation generated in docs/"

serve: check-uv
	@echo "Starting local server on http://localhost:8000"
	@echo "Press Ctrl+C to stop the server"
	@cd docs && uv run python -m http.server 8000

clean:
	@echo "Cleaning generated files..."
	@rm -f docs/data.json
	@echo "✓ Cleaned!"

test: validate generate
	@echo ""
	@echo "Running verification checks..."
	@./scripts/test_local.sh
	@echo ""
	@echo "✓ All tests passed!"
	@echo ""
	@echo "To view the site locally, run: make serve"

test-full: test
	@echo ""
	@echo "Opening browser and starting server..."
	@(sleep 2 && open http://localhost:8000) &
	@make serve

update: validate generate
	@echo "✓ Documentation updated successfully!"
