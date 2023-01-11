
build: test
	python3 -m build

test:
	python3 -m unittest discover

clean:
	rm -rf dist
