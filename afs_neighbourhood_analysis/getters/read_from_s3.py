import pandas as pd
import logging
import boto3
from botocore.exceptions import ClientError
import tempfile

BUCKET = "afs-neighbourhood-analysis"

logger = logging.getLogger(__name__)


def s3_exists(path, bucket=BUCKET):
    """Checks whether `afs-neighbourhood-analysis/data/{path}` exists in `BUCKET`
    Args:
        path (str): Path to file after ``afs-neighbourhood-analysis/data` in `project_dir`
    Returns:
        bool
    """

    path = "data/" + path
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket=bucket, Key=path)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            print(e.response)
            raise e


def data_from_s3(path, filename, bucket=BUCKET):
    if s3_exists(path) == True:
        object_path = "data/" + path

        s3 = boto3.client("s3")
        return s3.download_file(BUCKET, object_path, filename)
    else:
        logging.warning(f"s3://{bucket}/data/{path} does not exist.")


def df_from_s3(path, bucket=BUCKET, **kwargs):
    """Download `afs-neighbourhood-analysis/data/{path}` from `BUCKET`
    Args:
        path (str): Path to file after in `project_dir`
            E.g. `path="afs-neighbourhood-analysis/data/access_to_healthy_hazards_and_assets/AHAH_V3.csv"` will
            fetch the s3 key
            `"s3://{BUCKET}/data/access_to_healthy_hazards_and_assets/AHAH_V3.csv"`
            to a pandas.DataFrame
    Returns:
        df (pandas.DataFrame): a pandas DataFrame of the original files.
    """
    temp = tempfile.NamedTemporaryFile()
    data_from_s3(path, temp.name, bucket=bucket)
    header = kwargs.get("header", 0)
    if ".xlsm" in path or ".xlsx" in path:
        sheet_name = kwargs.get("sheet_name", "AHAH Overall Index and Domains ")
        usecols = kwargs.get("usecols", None)
        df = pd.read_excel(
            temp.name, sheet_name=sheet_name, header=header, usecols=usecols
        )
    else:
        index_col = kwargs.get("index_col", None)
        df = pd.read_csv(temp.name, header=header, index_col=index_col)

    return df
