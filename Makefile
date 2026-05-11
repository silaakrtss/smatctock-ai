.PHONY: install test lint format format-check typecheck imports check run \
        migrate seed bootstrap clean

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

typecheck:
	mypy src/

imports:
	lint-imports

check: lint format-check typecheck imports test

# --- DB lifecycle -----------------------------------------------------------

migrate:
	@mkdir -p data
	alembic upgrade head

seed:
	python -m src.infrastructure.db.seed_cli

# `make bootstrap` ilk klonlamada bir kez çalıştırılır:
# bağımlılıkları kurar, DB şemasını uygular, dev seed'i ekler.
bootstrap: install migrate seed
	@echo "✓ bootstrap tamam — make run ile sunucuyu başlat"

# --- Sunucu -----------------------------------------------------------------

# 127.0.0.1:8000 üzerinde dev modunda; template ve kod değişikliklerini
# otomatik yakalar.
run:
	uvicorn src.presentation.main:app \
		--host 127.0.0.1 --port 8000 \
		--reload --reload-include "*.html"

# --- Temizlik ---------------------------------------------------------------

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +

# DB'yi sıfırlamak için: dosyayı sil + migrate + seed
reset-db:
	rm -f data/app.db data/app.db-shm data/app.db-wal
	$(MAKE) migrate
	$(MAKE) seed
