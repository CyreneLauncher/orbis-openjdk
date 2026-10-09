"""Read OpenJDK link records in the build directory that produced them."""
from pathlib import Path
import shlex


def recorded_objects(tokens, build_root, responses=frozenset()):
    root = Path(build_root).resolve()
    objects = []
    for token in tokens:
        if token.startswith('@'):
            response = (root / token[1:]).resolve()
            if response in responses or len(responses) >= 8:
                raise ValueError('Recursive object response file: ' + str(response))
            objects.extend(recorded_objects(shlex.split(response.read_text()), root,
                                            responses | {response}))
        elif token.endswith('.o') and not token.startswith('-'):
            path = (root / token).resolve()
            if not path.is_file():
                raise ValueError('Recorded build object is missing: ' + str(path))
            objects.append(path)
    return objects
