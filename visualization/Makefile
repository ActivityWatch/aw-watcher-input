.PHONY: build clean

build: dist/index.html dist/bundle.js

clean:
	rm -r dist

dist/bundle.js: src/index.js
	browserify $< -o $@

dist/index.html: src/index.pug
	pug src/index.pug -o dist/
