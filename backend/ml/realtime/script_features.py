import os


def extract_script_features(file_path):

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        lines = code.split("\n")

        file_size = len(code) / 10000  # normalize
        line_count = len(lines) / 1000

        import_count = sum(1 for l in lines if "import" in l)
        function_count = sum(1 for l in lines if "def " in l)
        class_count = sum(1 for l in lines if "class " in l)

        # Normalize
        import_count /= 50
        function_count /= 50
        class_count /= 20

        # Language encoding
        if file_path.endswith(".py"):
            language = 0
        elif file_path.endswith(".java"):
            language = 1
        else:
            language = 0

        return [
            file_size,
            line_count,
            import_count,
            function_count,
            class_count,
            language
        ]

    except:
        return [0, 0, 0, 0, 0, 0]
