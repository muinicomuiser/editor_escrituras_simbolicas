pack-linux:
	.venv/bin/python3 -m PyInstaller \
	-y \
	bundle/specs/linux.spec \
	&& rm -r build
