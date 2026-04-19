.PHONY: validate-skill validate-skills test-skill-validators

SKILLS_ROOT ?= skills
SKILL ?=

validate-skill:
	@if [ -z "$(SKILL)" ]; then \
		echo "Usage: make validate-skill SKILL=path/to/skill"; \
		exit 1; \
	fi
	python scripts/quick_validate.py $(SKILL)

validate-skills:
	python scripts/validate_all_skills.py $(SKILLS_ROOT)

test-skill-validators:
	python -m pytest tests/tools/test_skills_validation.py -q
