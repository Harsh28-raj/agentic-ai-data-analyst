import glob

for filepath in glob.glob("frontend/pages/*.py"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace literal escape sequences with actual characters
    content = content.replace("\\n", "\n")
    content = content.replace("\\t", "\t")
    content = content.replace("\\r", "\r")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Fixed syntax corruption.")
