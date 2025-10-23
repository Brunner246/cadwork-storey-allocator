import os
import zipfile
from pathlib import Path


def create_zip():
    base_dir = os.getcwd()
    zip_name = 'storey_allocator.zip'

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zip_main_file(zipf)
        zip_src_directory(base_dir, zipf)
        zip_site_packages(zipf)

    print(f"Created {zip_name}")


def zip_site_packages(zipf: zipfile.ZipFile):
    site_packages_dir = Path(__file__).parent / '.venv' / 'Lib' / 'site-packages'
    compas_path = site_packages_dir / 'compas'
    if os.path.exists(compas_path):
        for root, dirs, files in os.walk(compas_path):
            # [:] modifies the list in place to avoid walking into __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, str(Path(__file__).parent))
                zipf.write(file_path, arcname)


def zip_src_directory(base_dir: str, zipf: zipfile.ZipFile):
    if os.path.exists('src'):
        for root, dirs, files in os.walk('src'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname)


def zip_main_file(zipf: zipfile.ZipFile):
    file = 'storey_allocator.py'
    if os.path.exists(file):
        zipf.write(file, file)


if __name__ == '__main__':
    create_zip()
