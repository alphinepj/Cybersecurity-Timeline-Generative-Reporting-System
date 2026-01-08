import os

def load_rag_context(base_path="rag"):
    context_blocks = []

    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".md"):
                with open(os.path.join(root, file), "r") as f:
                    context_blocks.append(f.read())

    return "\n\n".join(context_blocks)
