import os

# Silence tqdm progress bars (model weight loading, batches, etc.) for the
# entire test session.  Must be set before any tqdm instance is created —
# pytest_configure runs before collection and import of test modules.


def pytest_configure(config):  # noqa: ARG001
    os.environ["TQDM_DISABLE"] = "1"
