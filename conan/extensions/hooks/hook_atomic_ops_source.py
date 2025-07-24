from conan.tools.files import load, save
import os

def pre_source(conanfile):
    print("hello from cedrik")
    # Check if the recipe is the one you want to modify
    if conanfile.name == "libatomic_ops" and conanfile.version == "7.8.2":
        # Load the conandata.yml
        conandata_path = os.path.join(conanfile.recipe_folder, "conandata.yml")
        if os.path.exists(conandata_path):
            conandata = load(conanfile, conandata_path)
            
            # Parse and modify the YAML content
            import yaml
            data = yaml.safe_load(conandata)
            if "sources" in data and conanfile.version in data["sources"]:
                data["sources"][conanfile.version]["url"] = "https://github.com/bdwgc/libatomic_ops/releases/download/v7.8.2/libatomic_ops-7.8.2.tar.gz"
                # Update the sha256 if the file content has changed
                data["sources"][conanfile.version]["sha256"] = "d305207fe207f2b3fb5cb4c019da12b44ce3fcbc593dfd5080d867b1a2419b51"
            
            # Save the modified conandata.yml back
            save(conanfile, conandata_path, yaml.safe_dump(data))
