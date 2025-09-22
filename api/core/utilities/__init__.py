try:
    import importlib.util
    import os

    spec = importlib.util.spec_from_file_location(
        "core_utilities",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "utilities.py"),
    )
    utilities_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utilities_module)

    batch_processor = utilities_module.batch_processor
except ImportError:

    class BatchProcessor:
        def __init__(self, batch_size=1000):
            self.batch_size = batch_size

    batch_processor = BatchProcessor()
