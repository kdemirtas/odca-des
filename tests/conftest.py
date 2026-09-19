def pytest_addoption(parser):
    parser.addoption("--write-golden", action="store_true",
                     help="re-record the golden fingerprints (only under a bug-fix decision)")
