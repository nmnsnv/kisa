
build: test
	python3 -m build

test:
	python3 -m unittest discover

clean:
	rm -rf dist

upload-test: clean build
	python3 -m twine upload --repository testpypi dist/*

upload-pypi: clean build
	python3 -m twine upload dist/*
