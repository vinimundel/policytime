import ast
from pathlib import Path


def test_domain_has_no_external_system_dependencies():
    forbidden = {
        "os",
        "pathlib",
        "requests",
        "httpx",
        "sqlalchemy",
        "torch",
        "langchain_core",
        "langchain_mistralai",
        "time",
        "policytime.adapters",
        "policytime.delivery",
    }
    for path in Path("src/policytime/domain").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            if isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            for module in modules:
                assert not any(
                    module == name or module.startswith(name + ".") for name in forbidden
                ), path


def test_application_does_not_depend_on_adapters_or_delivery():
    for path in Path("src/policytime/application").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(("policytime.adapters", "policytime.delivery")), (
                    path
                )
