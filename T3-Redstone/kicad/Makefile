# T3-Redstone uretim zinciri (KiCad 7 pcbnew Python'u gerekir)
#   make            -> kart + yonlendirme + sema + belgeler
#   make board      -> yalnizca yerlesim + guc (rs_design.py degisince)
# Freerouting: https://repo1.maven.org/maven2/app/freerouting/freerouting/2.4.1/
#   FREEROUTING_JAR=/yol/freerouting-2.4.1-executable.jar  JAVA=/yol/java (25+)
PY ?= /usr/bin/python3

.PHONY: all board route sch docs render clean
all: board route sch docs

board:
	$(PY) rs_build.py

route:
	$(PY) rs_route.py

sch:
	$(PY) rs_sch.py --check

docs:
	$(PY) rs_bom.py
	$(PY) rs_docs.py
	$(PY) rs_render.py

clean:
	rm -rf build __pycache__
