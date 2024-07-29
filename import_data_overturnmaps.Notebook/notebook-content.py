# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "3a2886ff-5b95-4a2d-85a1-96230d013faa",
# META       "default_lakehouse_name": "storage",
# META       "default_lakehouse_workspace_id": "8f32a310-5334-46e7-badd-1eb3a5490821",
# META       "known_lakehouses": [
# META         {
# META           "id": "3a2886ff-5b95-4a2d-85a1-96230d013faa"
# META         }
# META       ]
# META     }
# META   }
# META }

# PARAMETERS CELL ********************

country_pr = 'CN'

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

!pip install duckdb

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import duckdb
# https://github.com/OvertureMaps/data/discussions/23#discussioncomment-7011246
duckdb.sql("install spatial;load spatial;")
duckdb.sql("install httpfs;load httpfs;")
duckdb.sql("set s3_region='us-west-2';")

bbox, wkt = duckdb.sql(f"""
select
    bbox,
    ST_AsText(ST_GeomFromWKB(geometry)) AS wkt
from read_parquet('s3://overturemaps-us-west-2/release/2024-07-22.0/theme=divisions/type=division_area/*', filename=true, hive_partitioning=1)
where
    country = '{country_pr}'
    AND subtype = 'country'
  """
).fetchall()[0]

df = duckdb.sql(f"""
select
id,
names.primary as name,
categories.primary as category,
ST_AsText(ST_GeomFromWKB(geometry)) AS wkt,
ST_X(ST_GeomFromWKB(geometry)) AS X,
ST_Y(ST_GeomFromWKB(geometry))  AS Y,
'{country_pr}' as country
from read_parquet('s3://overturemaps-us-west-2/release/2024-07-22.0/theme=places/type=*/*', filename=true, hive_partitioning=1)
where
    bbox.xmin <= {bbox["xmax"]}
    AND bbox.xmax >= {bbox["xmin"]}
    AND bbox.ymin <= {bbox["ymax"]}
    AND bbox.ymax >= {bbox["ymin"]} 
    AND ST_Intersects(ST_GeomFromText('{wkt}'), ST_GeomFromWKB(geometry));
"""
).df()
spark.createDataFrame(df).write.mode("overwrite").format("delta").saveAsTable("overturemaps")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.sql('select distinct category as category from overturemaps where category is not null')
df.write.mode("overwrite").format("delta").saveAsTable("category")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
