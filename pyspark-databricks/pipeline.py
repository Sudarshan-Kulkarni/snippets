import os
from pathlib import Path
from databricks.connect import DatabricksSession
from pyspark.sql import Window
from pyspark.sql import functions as F

# Load .env without external dependencies
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

UPSTREAM_TABLE = os.getenv("UPSTREAM_TABLE", "samples.nyctaxi.trips")


def create_spark_session():
    """Creates a remote SparkSession on Databricks Serverless Compute."""
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    if not host or not token:
        raise ValueError(
            "Missing DATABRICKS_HOST or DATABRICKS_TOKEN. "
            "Copy .env.example to .env and fill in your Databricks workspace URL and PAT."
        )

    print(f"Connecting to Databricks Serverless at {host} ...")
    return (
        DatabricksSession.builder
        .remote(host=host, token=token)
        .serverless(True)
        .getOrCreate()
    )


def transform_trips(raw_df):
    """
    Performs core PySpark DataFrame operations on the upstream NYC Taxi dataset:
      1. Filter out invalid/zero-distance or zero-fare records
      2. Derive `trip_duration_mins` and `fare_per_mile`
      3. Rank trips within each `pickup_zip` using a Window function
      4. Aggregate metrics per `pickup_zip`
    """
    # 1. Filter & clean
    cleaned_df = raw_df.filter(
        (F.col("trip_distance") > 0)
        & (F.col("fare_amount") > 0)
        & F.col("pickup_zip").isNotNull()
    )

    # 2. Feature engineering
    enriched_df = (
        cleaned_df.withColumn(
            "trip_duration_mins",
            (
                F.unix_timestamp("tpep_dropoff_datetime")
                - F.unix_timestamp("tpep_pickup_datetime")
            )
            / 60.0,
        )
        .withColumn(
            "fare_per_mile",
            F.round(F.col("fare_amount") / F.col("trip_distance"), 2),
        )
        .filter(F.col("trip_duration_mins") > 0)
    )

    # 3. Window function: rank trips by fare within each pickup_zip
    zip_window = Window.partitionBy("pickup_zip").orderBy(F.desc("fare_amount"))
    ranked_df = enriched_df.withColumn("fare_rank_in_zip", F.row_number().over(zip_window))

    # 4. GroupBy aggregation per pickup_zip
    summary_df = (
        ranked_df.groupBy("pickup_zip")
        .agg(
            F.count("*").alias("total_trips"),
            F.round(F.avg("trip_distance"), 2).alias("avg_distance_miles"),
            F.round(F.avg("trip_duration_mins"), 2).alias("avg_duration_mins"),
            F.round(F.avg("fare_amount"), 2).alias("avg_fare_usd"),
            F.round(F.max("fare_amount"), 2).alias("max_fare_usd"),
            F.round(F.avg("fare_per_mile"), 2).alias("avg_fare_per_mile"),
        )
        .filter(F.col("total_trips") >= 20)
        .orderBy(F.desc("total_trips"))
    )

    return summary_df


def resolve_downstream_table(spark) -> str:
    """Places the output table under `sandbox` (supports `sandbox` as either a catalog or schema)."""
    if os.getenv("DOWNSTREAM_TABLE"):
        return os.getenv("DOWNSTREAM_TABLE")

    catalogs = [row.catalog for row in spark.sql("SHOW CATALOGS").collect()]
    if "sandbox" in catalogs:
        return "sandbox.default.nyctaxi_zip_summary"

    current_catalog = os.getenv("DATABRICKS_CATALOG") or spark.catalog.currentCatalog()
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{current_catalog}`.`sandbox`")
    return f"{current_catalog}.sandbox.nyctaxi_zip_summary"


def run_pipeline():
    spark = create_spark_session()
    print(f"Connected! Spark version: {spark.version}\n")

    downstream_table = resolve_downstream_table(spark)

    # 1. Read upstream dataset
    print(f"1. Reading upstream dataset: {UPSTREAM_TABLE}")
    upstream_df = spark.read.table(UPSTREAM_TABLE)
    print(f"   Upstream row count: {upstream_df.count():,}\n")

    # 2. Transform dataset
    print("2. Running PySpark transformations (filter, derived columns, window rank, groupBy)...")
    transformed_df = transform_trips(upstream_df)

    # 3. Write to downstream Delta table
    print(f"3. Writing transformed dataset to downstream Delta table: {downstream_table}")
    (
        transformed_df.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(downstream_table)
    )
    print("   Write complete!\n")

    # 4. Verify downstream dataset by querying it back
    print(f"4. Verifying downstream dataset ({downstream_table}):")
    verify_df = spark.read.table(downstream_table)
    print(f"   Downstream row count: {verify_df.count():,}")
    verify_df.show(10, truncate=False)


if __name__ == "__main__":
    run_pipeline()
