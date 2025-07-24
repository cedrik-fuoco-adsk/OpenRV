from conan import ConanFile
from conan.tools.files import load, save
import os

class ZlibWrapper(ConanFile):
    name = "libatomic_ops"
    version = "7.8.2"
    requires = "libatomic_ops/7.8.2"

    def export_sources(self):
        self.copy("conandata.yml")

    def source(self):
        conandata_path = os.path.join(self.recipe_folder, "conandata.yml")
        if os.path.exists(conandata_path):
            conandata = load(self, conandata_path)
            import yaml
            data = yaml.safe_load(conandata)
            if "sources" in data and self.version in data["sources"]:
                data["sources"][self.version]["url"] = "https://github.com/bdwgc/libatomic_ops/releases/download/v7.8.2/libatomic_ops-7.8.2.tar.gz"
                data["sources"][self.version]["sha256"] = "d305207fe207f2b3fb5cb4c019da12b44ce3fcbc593dfd5080d867b1a2419b51"
            save(self, conandata_path, yaml.safe_dump(data))
        super().source()
