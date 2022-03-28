"""
Functions to retrieve, unzip and download the education statistics regarding Early Years (in particular Good Levels of Development outcomes and the Early Years provision)
"""


from bs4 import BeautifulSoup, SoupStrainer
import json
import os
import requests
from io import BytesIO
from zipfile import ZipFile
import pandas as pd

from afs_neighbourhood_analysis import PROJECT_DIR


def get_urls(**kwargs):
    """
    Function for retrieving the dataset urls from the gov.uk website.

    Returns:
        array of urls
    """
    url = kwargs.get(
        "url",
        "https://www.gov.uk/government/collections/statistics-early-years-foundation-stage-profile",
    )

    req = requests.get(url).content

    try:
        soup = BeautifulSoup(req, "html.parser")

        data = json.loads(soup.find("script", type="application/ld+json").string)
        return [data["hasPart"][x]["sameAs"] for x in range(len(data["hasPart"]))]
    except:
        pass
    try:
        keyword = kwargs.get("keyword", "provision")
        return [
            link["href"]
            for link in BeautifulSoup(
                req, parse_only=SoupStrainer("a"), features="html.parser"
            )
            if hasattr(link, "href")
            if keyword in link["href"] and "https" in link["href"]
        ]
    except:
        print("Failed to get URLS")
        pass


def get_links(url_):
    """
    Function for retrieving the individual dataset urls from a EYFSP webpage (see function get_urls_eyfsp).

    Returns:
        array of the urls of the individual datasets
    """
    req = requests.get(url_).content
    return [
        link["href"]
        for link in BeautifulSoup(
            req, parse_only=SoupStrainer("a"), features="html.parser"
        )
        if hasattr(link, "href")
        if ".zip" in link["href"]
    ]


def unzip_file_links(zip_url, **kwargs):
    """
    Function to take the URLs of the Early Years datasets and unzip them, extracting the relevant files to /inputs/data/aux.
    """
    folder_name = kwargs.get("folder_name", "eyfsp")
    extensions = kwargs.get("extensions", (".csv", ".xlsx"))
    mute = kwargs.get("mute", False)

    member_files = kwargs.get("member_files", None)

    req = requests.get(zip_url)
    files = ZipFile(BytesIO(req.content))

    if member_files is None:
        files_to_extract = [
            file_ for file_ in files.namelist() if file_.endswith(extensions)
        ]
        if mute == False:
            print(f"files extracted : {files_to_extract}")
        # Writing the zip file into local file system
        files.extractall(
            f"{PROJECT_DIR}/inputs/data/aux/{folder_name}", members=files_to_extract
        )
    else:
        try:
            extract_files = [
                member_file_
                for member_file_ in member_files
                if member_file_ in files.namelist()
            ]
            files.extractall(
                f"{PROJECT_DIR)}/inputs/data/aux/{folder_name}", members=extract_files
            )
        except:
            pass


def get_data(**kwargs):
    """
    Get the data from the DfE website regarding the Early Years: find the relevant URLs, unzip the files and extract to inputs/data/aux
    """

    urls = get_urls(**kwargs)
    
    for url_ in urls:
        dataset_links = get_links(url_)
        for link_ in dataset_links:
            unzip_file_links(link_, **kwargs)
