##################################################################################
# OCR and Document Categorization Script
# 
# Description:
# This script performs OCR (Optical Character Recognition) on various file types 
# (PDF, images, etc.) and categorizes them using the Hrflow Dynamic Tagger API. It supports multiple 
# document types and applies predefined or custom labels for categorization.
# Packages to install: tqdm,requests
# Usage:
# Run the script with the following command:
#
# python script_ocr_and_categorize_a_doc.py hrflow_user_email hrflow_secret_key "path/to/document" --labels resume coverletter references diploma certificate permit license passport
#
# Parameters:
#   - hrflow_user_email  : Your Hrflow API user email.
#   - hrflow_secret_key  : Your Hrflow API secret key.
#   - path/to/document   : The path to the folder containing the documents to process.
#   - --labels           : A list of labels to use for categorization. 
#                         Default labels are: resume, coverletter, references, diploma, 
#                         certificate, permit, license, passport.
#                         You can customize this list by providing labels separated by spaces.
#
# Example:
# python script_ocr_and_categorize_a_doc.py your_email your_secret_key "/path/to/documents" --labels resume coverletter
#
# Author: [Abdellahi Mezid]
# Version: 1.0
##################################################################################


import os
import requests
import argparse

from tqdm import tqdm

VALID_EXTENSIONS = [
    ".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".doc", ".docx", ".rtf",
    ".dotx", ".odt", ".odp", ".ppt", ".pptx", ".msg"
]
INVALID_FILENAMES = [".", ".."]

def is_valid_extension(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return ext in VALID_EXTENSIONS

def is_valid_filename(file_path):
    name = os.path.basename(file_path)
    return name not in INVALID_FILENAMES

def get_files_from_dir(dir_path, is_recursive=True):
    file_res = []
    files_path = os.listdir(dir_path)
    for file_path in files_path:
        true_path = os.path.join(dir_path, file_path)
        if os.path.isdir(true_path) and is_recursive:
            if is_valid_filename(true_path):
                file_res += get_files_from_dir(true_path, is_recursive)
        elif is_valid_extension(true_path):
            file_res.append(true_path)
    return file_res

def perform_ocr(api_user, api_secret, file_path):
    url = "https://api.hrflow.ai/v1/text/ocr"
    headers = {
        'X-USER-EMAIL': api_user,
        'X-API-KEY': api_secret
    }
    try:
        with open(file_path, "rb") as file:
            filename = os.path.basename(file_path)
            files = [('file', (filename, file, 'application/pdf'))]
            response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response.json()["data"]["text"]
    except Exception as e:
        print(f"Error while OCR {file_path}: {e}")
        return None

def tag_text(api_user, api_secret, text, labels, context=""):
    url = "https://api.hrflow.ai/v1/text/tagging"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": api_secret,
        "X-USER-EMAIL": api_user,
    }
    payload = {
        "algorithm_key": "tagger-hrflow-dynamic",
        "texts": [text],
        "dynamic_labels": labels,
        "top_n": 1,
        "dynamic_context": context
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data["data"] and "tags" in data["data"][0]:
            return data["data"][0]["tags"][0]
        return None
    except Exception as e:
        print(f"Error while tagging : {e}")
        return None

def main(api_user, api_secret, files_folder, labels):
    files_list = get_files_from_dir(files_folder, is_recursive=True)
    failed = []

    for file_path in tqdm(files_list, desc="Files processing in progress"):
        ocr_text = perform_ocr(api_user, api_secret, file_path)
        if not ocr_text:
            failed.append(file_path)
            continue
        
        tag = tag_text(api_user, api_secret, ocr_text, labels)
        print(f"File : {file_path} -> Tag : {tag if tag else 'No categorization'}")

    if failed:
        print(f"\nFailed files ({len(failed)}) :")
        for f in failed:
            print(f" - {f}")

def parse_args():
    parser = argparse.ArgumentParser(description="OCR and document categorization")
    parser.add_argument("api_user", help="API user email")
    parser.add_argument("api_secret", help="API secret key")
    parser.add_argument("files_folder", help="Path to the folder containing the files to process")
    parser.add_argument("--labels", nargs="*", default=["resume", "coverletter", "references", "diploma", "certificate", 
                                                       "permit", "license", "passport"], 
                        help="List of labels to use for categorization")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.api_user, args.api_secret, args.files_folder, args.labels)