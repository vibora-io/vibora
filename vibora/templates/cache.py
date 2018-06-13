import os
from typing import Set, Dict

from .compilers.base import TemplateCompiler
from .template import CompiledTemplate
from .utils import CompilationResult, TemplateMeta


class TemplateCache:

    def __init__(self):
        self.loaded_templates = {}
        self.loaded_metas = {}

    def store(self, compiled: CompilationResult):
        raise NotImplementedError

    def remove(self, template_hash: str):
        raise NotImplementedError

    def get(self, template_hash: str):
        raise NotImplementedError

    def load_templates(self):
        raise NotImplementedError

    def clean(self, useful_hashes: set):

        # Fixing relationships.
        death_queue = set()
        while True:
            initial_count = len(death_queue)
            # Detecting updated parents, so their children must be updated.
            for meta in self.loaded_metas.values():
                for template_hash in meta.dependencies:
                    if template_hash not in useful_hashes:
                        death_queue.add(meta.template_hash)
                        self.remove(meta.template_hash)
            if initial_count == len(death_queue):
                break

        # Removing lonely unused templates
        for template_hash in list(self.loaded_templates.keys()):
            if template_hash not in useful_hashes:
                self.remove(template_hash)


class InMemoryCache(TemplateCache):

    def __init__(self):
        super().__init__()
        self.loaded_templates: Dict[str, CompiledTemplate] = {}

    def get(self, template_hash: str) -> CompiledTemplate:
        """

        :param template_hash:
        :return:
        """
        return self.loaded_templates.get(template_hash)

    def store(self, compiled: CompiledTemplate):
        """

        :param compiled:
        :return:
        """
        self.loaded_templates[compiled.meta.template_hash] = compiled
        self.loaded_metas[compiled.meta.template_hash] = compiled.meta

    def remove(self, template_hash: str):
        """

        :param template_hash:
        :return:
        """
        try:
            del self.loaded_templates[template_hash]
        except KeyError:
            pass
        try:
            del self.loaded_metas[template_hash]
        except KeyError:
            pass

    def load_templates(self):
        pass


class DiskCache(TemplateCache):

    def __init__(self, directory: str, compiler: TemplateCompiler, meta_suffix='.json'):
        super().__init__()
        self.directory = os.path.join(directory, '__cache__', compiler.NAME)
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.compiler = compiler
        self.meta_suffix = meta_suffix
        self.loaded_templates = {}

    def _load_template(self, meta_path: str) -> bool:
        """

        :param meta_path:
        :return:
        """
        compiled_template_path = meta_path.replace(self.meta_suffix, '')

        # Loading the meta file.
        try:
            meta = TemplateMeta.load_from_path(meta_path)
        except (FileNotFoundError, ValueError):
            # If the meta file is unreadable let's just delete it to refresh the cache.
            # Maybe the file was deleted. Let's just check if the template is orphan and fix this.
            try:
                os.remove(compiled_template_path)
            except FileNotFoundError:
                pass
            return False

        # Checking if the cached version is up to date.
        if meta.compiler != self.compiler.NAME or meta.version != self.compiler.VERSION:
            # It may happen when Vibora is updated and the compiler has been changed.
            # In this case the cached template is no longer valid.
            try:
                os.remove(compiled_template_path)
            except FileNotFoundError:
                pass
            return False

        try:
            with open(compiled_template_path, 'rb') as f:
                self.loaded_templates[meta.template_hash] = self.compiler.load_compiled_template(meta, f.read())
                self.loaded_metas[meta.template_hash] = meta
                return True
        except FileNotFoundError:
            try:
                os.remove(meta_path)
            except FileNotFoundError:
                pass

        return False

    def store(self, compiled: CompilationResult):
        """

        :param compiled:
        :return:
        """
        self.loaded_templates[compiled.meta.template_hash] = compiled.render_function
        self.loaded_metas[compiled.meta] = compiled.meta
        path = os.path.join(self.directory, compiled.meta.template_hash)
        meta_path = path + self.meta_suffix
        with open(path, 'wb') as f:
            f.write(compiled.code)
        compiled.meta.store(meta_path)

    def load_templates(self):
        """

        :return:
        """
        useful_files = []
        files = set(os.listdir(self.directory))

        for filename in files:
            if filename.endswith(self.meta_suffix):
                meta_path = os.path.join(self.directory, filename)
                if self._load_template(meta_path):
                    template_path = os.path.join(self.directory, filename.replace(self.meta_suffix, ''))
                    useful_files.append(os.path.basename(template_path))
                    useful_files.append(os.path.basename(meta_path))

        for useless_filename in (files - set(useful_files)):
            try:
                os.remove(os.path.join(self.directory, useless_filename))
            except FileNotFoundError:
                pass

    def remove(self, template_hash: str):
        try:
            os.remove(os.path.join(self.directory, template_hash))
        except FileNotFoundError:
            pass
        try:
            os.remove(os.path.join(self.directory, template_hash + self.meta_suffix))
        except FileNotFoundError:
            pass
        try:
            del self.loaded_templates[template_hash]
        except KeyError:
            pass
        try:
            del self.loaded_metas[template_hash]
        except KeyError:
            pass

    def get(self, template_hash: str):
        return self.loaded_templates.get(template_hash)
