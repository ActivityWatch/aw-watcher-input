.PHONY: build test package clean

build:
	poetry install

test:
	poetry run aw-watcher-input --help  # Ensures that it at least starts
	make typecheck

typecheck:
	poetry run mypy src/aw_watcher_input --ignore-missing-imports

package:
	pyinstaller aw-watcher-input.spec --clean --noconfirm

clean:
	rm -rf build dist
	rm -rf aw_watcher_input/__pycache__
