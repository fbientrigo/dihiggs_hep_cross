.PHONY: test inventory tidy toy paper-proxy figures figures-v2 chat-json diphoton-extract diphoton-package diphoton-2hdmc-bridge madgraph-prepare sigma-apply madgraph-sigma all clean

PYTHONPATH := src

test:
	PYTHONPATH=$(PYTHONPATH) pytest

inventory:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/01_hepdata_inventory.py

tidy:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/02_hepdata_tidy_extract.py

toy:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/02_toy_s_recast.py

paper-proxy:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/03_paper_s_benchmark_proxy.py

figures:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/04_make_paper_aware_figures.py

figures-v2:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/05_make_interpretation_figures.py

chat-json:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/06_export_chat_summaries.py

diphoton-extract:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/07_diphoton_hepdata_extract.py

diphoton-package:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/08_diphoton_meeting_package.py

diphoton-2hdmc-bridge:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/09_link_2hdmc_to_diphoton.py $(DIPHOTON_2HDMC_ARGS)

madgraph-prepare:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/12_prepare_madgraph_runs.py $(MADGRAPH_PREPARE_ARGS)

sigma-apply:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/10_apply_sigma_inputs.py $(SIGMA_APPLY_ARGS)

madgraph-sigma:
	PYTHONPATH=$(PYTHONPATH) python3 scripts/11_ingest_madgraph_xsec.py $(MADGRAPH_SIGMA_ARGS)

all: test inventory tidy toy paper-proxy figures figures-v2 chat-json diphoton-extract diphoton-package

clean:
	rm -rf outputs .pytest_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
