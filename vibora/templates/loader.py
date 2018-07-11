import time
import os
import threading
from .engine import TemplateEngine
from .template import Template
from .utils import get_import_names


class TemplateLoader(threading.Thread):
    def __init__(
        self,
        directories: list,
        engine: TemplateEngine,
        supported_files: list = None,
        interval: int = 0.5,
    ):
        super().__init__()
        self.directories = directories
        self.engine = engine
        self.supported_files = supported_files or (".html", ".vib")
        self.cache = {}
        self.path_index = {}
        self.hash_index = {}
        self.interval = interval
        self.has_to_run = True

    def reload_templates(self, paths: list):
        for root, path in paths:
            if path in self.path_index:
                template = self.path_index[path]

                # Searching for templates who depends on this one.
                relationships = []
                for meta in self.engine.cache.loaded_metas.values():
                    if template.hash in meta.dependencies:
                        relationships.append(meta.template_hash)

                # In case we found dependencies we need to reload them too.
                for template_hash in relationships:
                    if template_hash in self.hash_index:
                        values = self.hash_index[template_hash]
                        self.engine.remove_template(values[2])
                        self.add_to_engine(values[0], values[1])

                # Removing the actual template.
                self.engine.remove_template(template)

            self.add_to_engine(root, path)
        self.engine.sync_cache()
        self.engine.compile_templates()

    def check_for_modified_templates(self):
        to_be_notified = []
        for path in self.directories:
            for root, dirs, files in os.walk(path):
                for file in [f for f in files if f.endswith(self.supported_files)]:
                    path = os.path.join(root, file)
                    try:
                        last_modified = os.path.getmtime(path)
                        if path in self.cache:
                            if self.cache[path] != last_modified:
                                to_be_notified.append((root, path))
                        else:
                            to_be_notified.append((root, path))
                        self.cache[path] = last_modified
                    except FileNotFoundError:
                        continue
        if to_be_notified:
            self.reload_templates(to_be_notified)

    def add_to_engine(self, root: str, path: str):
        with open(path, "r") as f:
            template = Template(f.read())
            names = get_import_names(root, path)
            template = self.engine.add_template(template, names=names)
            self.path_index[path] = template
            self.hash_index[template.hash] = (root, path, template)

    def load(self):
        for directory in self.directories:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(self.supported_files):
                        path = os.path.join(root, file)
                        self.add_to_engine(root, path)

    def run(self):
        while self.has_to_run:
            self.check_for_modified_templates()
            time.sleep(self.interval)
