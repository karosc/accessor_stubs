import glob
import json
import os
import pathlib
import zipfile

__HERE__ = pathlib.Path(__file__).parent
__ROOT__ = __HERE__.parent

dist_pattern = __ROOT__ / "dist" / "*.whl"

stub_files = ["xarray-stubs/core/dataarray.pyi", "xarray-stubs/core/dataset.pyi"]

base_versions = {"xarray": "0.0.0"}
__VERSION_FILE_PATH = __ROOT__ / "src" / "accessor_stubs" / "versions.json"


def remove_files_from_zip(zip_file, files_to_remove):
    # Create a temporary file to write the updated archive
    temp_zip_file = zip_file + ".tmp"

    # Open the original zip file for reading
    with zipfile.ZipFile(zip_file, "r") as original_zip:
        # Open the temporary zip file for writing
        with zipfile.ZipFile(temp_zip_file, "w") as temp_zip:
            # Copy all files from the original zip to the temporary zip except for those to remove
            for item in original_zip.infolist():
                if item.filename not in files_to_remove:
                    temp_zip.writestr(item, original_zip.read(item.filename))

    # Replace the original zip file with the temporary one
    os.replace(temp_zip_file, zip_file)


if __name__ == "__main__":
    os.chdir(__ROOT__)

    # create empty stubfilesk
    for file in stub_files:
        src_path = os.path.join("src", file)
        with open(src_path, "w"):
            pass

    with open(__VERSION_FILE_PATH, "w") as f:
        json.dump(base_versions, f)
    os.system("hatch build")

    # remove empty stub files
    dists = glob.glob(str(dist_pattern))
    for dist in dists:
        remove_files_from_zip(str(dist), stub_files)
    for file in stub_files:
        src_path = os.path.join("src", file)
        os.remove(src_path)
