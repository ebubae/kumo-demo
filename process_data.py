from typing import Literal
import polars as pl

from env import AWS_ACCESS_KEY, AWS_SECRET_KEY, engine
from tqdm import trange

ARTICLES_URI = "s3://kumo-public-datasets/hm_with_images/articles/part-00000-63ea08b0-f43e-48ff-83ad-d1b7212d7840-c000.snappy.parquet"
CUSTOMERS_URI = "s3://kumo-public-datasets/hm_with_images/customers/part-00000-9b749c0f-095a-448e-b555-cbfb0bb7a01c-c000.snappy.parquet"
TRANSACTIONS_URI = "s3://kumo-public-datasets/hm_with_images/transactions/part*snappy.parquet"

CHUNK_SIZE = 10_000

storage_opts = {
    "aws_access_key_id": AWS_ACCESS_KEY,
    "aws_secret_access_key": AWS_SECRET_KEY,
    "region": "us-west-2",
}

articles_df = pl.read_parquet(ARTICLES_URI, storage_options=storage_opts)


def write_to_db(table_name: Literal["articles", "customers", "transactions"]):
    uri_map = {
        "articles": ARTICLES_URI,
        "customers": CUSTOMERS_URI,
        "transactions": TRANSACTIONS_URI,
    }
    
    print(f"Reading S3 data for {table_name}...")
    df = pl.read_parquet(uri_map[table_name], storage_options=storage_opts)
    print(f"Writing to {table_name} table in Planetscale...")
    for i in trange(0, len(articles_df), CHUNK_SIZE):
        chunk = df.slice(i, CHUNK_SIZE)
        chunk.write_database(table_name, engine, if_table_exists="append")


write_to_db("articles")
write_to_db("customers")
write_to_db("transactions")
