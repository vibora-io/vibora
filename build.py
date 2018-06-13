import os
import sys
import subprocess

project_path = os.path.join(os.path.dirname(__file__), 'vibora')

# Seeking for files pending compilation.
pending_compilation = set()
for root, dirs, files in os.walk(project_path):
    for file in files:
        if file.endswith('.pyx'):
            pending_compilation.add(os.path.join(root, file))
        elif file.endswith('.py'):
            if (file[:-3] + '.pxd') in files:
                pending_compilation.add(os.path.join(root, file))
        elif file.endswith(('.so', '.c', '.html')):
            os.remove(os.path.join(root, file))

# Calling Cython to compile our extensions.
cython = os.path.join(os.path.dirname(sys.executable), 'cython')
process = subprocess.run([cython] + list(pending_compilation) + ['--fast-fail'])
if process.returncode != 0:
    raise SystemExit(f'Failed to compile .pyx files to C.')

# Building native extensions.
process = subprocess.run(
    [
        sys.executable,
        os.path.join(os.path.dirname(project_path), 'setup.py'),
        'build_ext',
        '--inplace'
    ]
)
if process.returncode != 0:
    raise SystemExit(f'Failed to build native modules.')

print('Build process completed successfully.')
