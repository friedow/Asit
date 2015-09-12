
import os
import shutil
import zipfile
import requests

class GithubUpdater:

    def __init__(self, author, project_name, actual_version):
        self.actual_version = actual_version
        self.project_url = "https://github.com/" + author + "/" + project_name + "/"
        self.latest_version = ""
        self.update_zip = ""
        self.update_dir = "./update"
        self.project_dir = "."

    def check(self):
        release_url = self.project_url + "releases"
        release_request = requests.get(release_url)
        begin_text = '<span class="tag-name">'
        begin = release_request.text.find(begin_text)

        if begin == -1:
            raise RuntimeWarning("There are no releases available for this project.")

        begin += len(begin_text)
        end = release_request.text.find('</span>', begin)
        self.latest_version = release_request.text[begin : end]
        if actual_version >= latest_version:
            return 0
        else:
            return 1

    def download(self):
        update_url = self.project_url + "archive/" + self.latest_version + ".zip"
        self.update_zip = self.latest_version + ".zip"
        with open(self.update_zip, "wb") as handle:
            try:
                download = requests.get(update_url, stream=True)
            except:
                raise RuntimeError("Download failed")

            if not download.ok:
                raise RuntimeError("Update could not be retrieved successfully.")

            for block in download.iter_content(1024):
                handle.write(block)

    def extract(self):
        try:
            with zipfile.ZipFile(self.update_zip, "r") as handle:
                handle.extractall(self.update_dir)
        except:
            raise RuntimeError("Extraction failed")

    def apply(self):
        try:
            for src_dir, dirs, files in os.walk(self.update_dir):
                dst_dir = src_dir.replace(self.update_dir, self.project_dir)
                if not os.path.exists(dst_dir):
                    os.mkdir(dst_dir)
                for file_ in files:
                    src_file = os.path.join(src_dir, file_)
                    dst_file = os.path.join(dst_dir, file_)
                    if os.path.exists(dst_file):
                        os.remove(dst_file)
                    shutil.move(src_file, dst_dir)
        except:
            raise RuntimeError("Critical update error")

    def clear(self):
        try:
            os.remove(self.update_zip)
            shutil.rmtree(self.update_dir)
        except:
            raise RuntimeError("Cant delete update files")
        return 0

    def update(self):
        try:
            print("[*] Checking for updates")
            if not self.check():
                print("[+] Script is already up to date")
                return 0
            print("[*] A new update is available")

            print("[*] Starting download")
            self.download()
            print("[+] Download finished successfully")

            print("[*] Extracting archive")
            self.extract()
            print("[+] Extraction finished successfully")

            print("[*] Updating content, do not cancel the script now")
            self.apply()
            print("[+] Update finished successfully")
        except Exception as e:
            print("[!] Update Error: " + str(e))
