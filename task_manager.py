import os
import shutil
from models import Task
from dotenv import load_dotenv
from download_links import extract_download_links
from gd import main_downloader as google_downloader
from helpers import description_extractor, download_href_links, system_chime

load_dotenv()

path = os.getenv("TASKFOLDERPASS")
dropboxFolder = os.getenv("DROPBOX")
aeFile = os.getenv("PROJECT")
aeFileName, ext = os.path.splitext(aeFile)


def setup_new_task(task: Task) -> None:
    # print(f"Discription: {task.description}")
    task_folder_path = os.path.join(path, task.name)
    dropbox_patch = os.path.join(dropboxFolder, task.name)
    # print(f"folder path is {task_folder_path}")

    if not os.path.exists(task_folder_path):
        os.makedirs(task_folder_path)
        if not os.path.exists(dropbox_patch):
            os.makedirs(dropbox_patch)


        shutil.copy2(os.path.join(path, aeFile), os.path.join(task_folder_path, f"{task.name}{ext}"))


        formatted_description = description_extractor(description=task.description, path=task_folder_path)
        download_href_links(task.description, task_folder_path)
        #parse tasks descrition
        download_links = extract_download_links(task.description)
        # print(f"download_links: {download_links}")
        #download folders
        if download_links:
            print(f"Found {len(download_links)} download links in task description.")
            for link in download_links:
                google_downloader(link, download_path=task_folder_path)
        else:
            print("No download links found in task description.")
        

        

        #fromat task description and put it into txt file

        #if there a links in discription, download files into folder

        #copy .aep project and rename it

        print("🎉 Done ")
        system_chime()
        

    else:
        print("Task folder already exists, skipping setup.")

    