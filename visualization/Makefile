.PHONY: build test clean

build: dist/index.html dist/bundle.js

test:
	npm test

clean:
	rm -r dist

dist/bundle.js: src/index.js src/aggregate.js package-lock.json
	mkdir -p dist
	npx browserify src/index.js -o $@

dist/index.html: src/index.pug
	mkdir -p dist
	node -e 'require("fs").writeFileSync("$@", require("pug").renderFile("$<"))'
