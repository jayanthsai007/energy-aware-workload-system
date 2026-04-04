import ast


# -------------------------
# PYTHON FEATURE EXTRACTION
# -------------------------
def extract_python_features(code: str):
    try:
        tree = ast.parse(code)
    except Exception:
        # fallback if parsing fails
        return default_features(language=0)

    functions = sum(isinstance(n, ast.FunctionDef) for n in ast.walk(tree))
    classes = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
    imports = sum(isinstance(n, (ast.Import, ast.ImportFrom))
                  for n in ast.walk(tree))

    line_count = len(code.splitlines())
    file_size = len(code)

    return {
        "file_size": normalize(file_size, 5000),
        "line_count": normalize(line_count, 500),
        "imports": normalize(imports, 20),
        "functions": normalize(functions, 50),
        "classes": normalize(classes, 20),
        "language": 0  # python
    }


# -------------------------
# JAVA FEATURE EXTRACTION
# -------------------------
def extract_java_features(code: str):

    line_count = len(code.splitlines())
    file_size = len(code)

    imports = code.count("import")
    classes = code.count("class")
    functions = code.count("void") + code.count("int") + code.count("String")

    return {
        "file_size": normalize(file_size, 5000),
        "line_count": normalize(line_count, 500),
        "imports": normalize(imports, 20),
        "functions": normalize(functions, 50),
        "classes": normalize(classes, 20),
        "language": 1  # java
    }


# -------------------------
# MAIN EXTRACTOR
# -------------------------
def extract_script_features(code: str, language: str):

    if language.lower() == "python":
        return extract_python_features(code)

    elif language.lower() == "java":
        return extract_java_features(code)

    else:
        return default_features(language=0)


# -------------------------
# HELPERS
# -------------------------
def normalize(value, max_value):
    return min(value / max_value, 1.0)


def default_features(language=0):
    return {
        "file_size": 0.5,
        "line_count": 0.5,
        "imports": 0.1,
        "functions": 0.2,
        "classes": 0.1,
        "language": language
    }
