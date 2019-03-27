# Databricks notebook source
configs = {"fs.azure.account.auth.type": "OAuth",
       "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
       "fs.azure.account.oauth2.client.id": "86642a93-7dc5-414a-86cc-3b377f8b5d7f",
       "fs.azure.account.oauth2.client.secret": "V/tHco8vmSDAjKKreCwg4ZRLdVrBVpqS9lekWuBtVeI=",
       "fs.azure.account.oauth2.client.endpoint": "https://login.microsoftonline.com/2eb86c1f-71e5-4dd8-850a-33058adc0996/oauth2/token",
       "fs.azure.createRemoteFileSystemDuringInitialization": "true"}
try:
  dbutils.fs.mount(
  source = "abfss://southridge@southridgeteam7v2.dfs.core.windows.net/",
  mount_point = "/mnt/southridge",
  extra_configs = configs)
except: 
  pass

# COMMAND ----------

import pyspark.sql.functions as fns
from pyspark.sql.functions import col, lit
import uuid
from pyspark.sql.types import StringType

uuidUdf = fns.udf(lambda : str(uuid.uuid1()), StringType())

# COMMAND ----------

dbutils.fs.ls("/mnt/southridge/")

# COMMAND ----------

vanActors = spark.read.format('csv').options(inferschema='true').load("/mnt/southridge/vanarsdelltd/onpremrentals/actors.csv")
vanActors = vanActors.select(
  col("_c0").alias("ActorID"),
  col("_c1").alias("ActorName"),
  col("_c2").alias("Gender"),
)
vanActors.show(2, False)

# COMMAND ----------

vanMovies = spark.read.format('csv').options(inferschema='true').load("/mnt/southridge/vanarsdelltd/onpremrentals/movies.csv")
vanMovies = vanMovies.select(
  col("_c0").alias("MovieID"),
  col("_c1").alias("MovieTitle"),
  col("_c2").alias("Genre"),
  col("_c3").alias("Rating"),
  col("_c4").alias("Runtime"),
  fns.to_date(col("_c5"), "MM-dd-yy").alias("ReleaseDate"),
  fns.substring(col("_c5"), 7, 4).cast("int").alias("AvailabilityYear")
)
vanMovies.show(2, False)

# COMMAND ----------

vanActors.show(2,False)

# COMMAND ----------

vanMovieActors = spark.read.format('csv').options(inferschema='true').load("/mnt/southridge/vanarsdelltd/onpremrentals/movieactors.csv")
vanMovieActors = vanMovieActors.select(
  col("_c0").alias("MovieActorID"),
  col("_c1").alias("MovieID"),
  col("_c2").alias("ActorID")
)
vanMovieActors.show(2, False)

# COMMAND ----------

vanCat = (vanMovies
               .join(vanMovieActors, on="MovieID")
               .join(vanActors, on="ActorID"))



vanCat = (vanCat
               .select(col("MovieID"),
                       col("MovieTitle"),
                       col("Genre").alias("Genre"),
                       col("Rating"),
                       lit(2).alias("SourceID"),
                       col("ReleaseDate").alias("AvailabilityDate"),
                       "AvailabilityYear",
                       "ActorID",
                       col("ActorName").alias("Actor"),
                       lit(None).cast("int").alias("MovieTier")).withColumn(
                 "CategoryID", uuidUdf()
               )
         )

vanCat.write.mode("overwrite").csv("/mnt/southridge/vanarsdelltd/output/catalog.csv")

#vanCat.show(2, False)

# COMMAND ----------

vanCust = spark.read.format('csv').options(inferschema='true').load("/mnt/southridge/vanarsdelltd/onpremrentals/customers.csv")

vanCust.show(2, False)

# COMMAND ----------

vanCustomer = (vanCust.selectExpr(
  "2 as SourceID",
  "_c0 as CustomerID",
  "_c3 as AddressLine1",
  "_c4 as AddressLine2",
  "_c5 as City", 
  "_c6 as State", 
  "_c7 as ZipCode",
  "_c9 as CreatedDate",
  "_c10 as UpdatedDate"
)).withColumn("AddressID", uuidUdf()
).select("*",fns.concat("SourceID", "CustomerID", "AddressID").alias("UniqueID"))

vanCustomer.write.mode("overwrite").csv("/mnt/southridge/vanarsdelltd/output/address.csv")
               
#vanCustomer.show(2, False)

# COMMAND ----------

vanCustomer = (vanCust.selectExpr(
  "2 as SourceID",
  "_c0 as CustomerID",
  "_c1 as FirstName",
  "_c2 as LastName",
  "cast(_c8 as string) as PhoneNumber", 
  "_c9 as CreatedDate",
  "_c10 as UpdatedDate"
)
).select("*",fns.concat("SourceID", "CustomerID").alias("UniqueID"))

vanCustomer.write.csv("/mnt/southridge/vanarsdelltd/output/customer.csv")
               
#vanCustomer.show(2, False)

# COMMAND ----------

fourTransactions = spark.read.format('csv').options(header='false', inferschema='true').load("/mnt/southridge/vanarsdelltd/onpremrentals/transactions.csv")

fourTransactions.show(4,False)

# COMMAND ----------

fourTrans = (fourTransactions.select(
  lit(2).alias("SourceID"),
  col("_c0").alias("TransactionID"),
  col("_c1").alias("CustomerID"),
  col("_c2").alias("MovieID"),
  fns.to_date(col("_c3").cast("string"), "yyyyMMdd").alias("RentalDate"),
  fns.to_date(col("_c4").cast("string"), "yyyyMMdd").alias("ReturnDate"),
  col("_c5").alias("RentalFee"),
  fns.when(col("_c6") == "\\N", lit(None)).otherwise(col("_c6")).alias("LateFee"),
  fns.when(col("_c7") == "True", lit(True)).otherwise(lit(False)).alias("RewindFlag"),
  col("_c8").alias("CreatedDate"),
  col("_c9").alias("UpdatedDate")
)).select(
  "*",
  fns.concat("SourceID", "TransactionID").alias("UniqueOrderID"),
  fns.concat("SourceID", "CustomerID").alias("SourceCustomerID"),
  fns.concat("SourceID", "MovieID").alias("SourceMovieID"))

#fourTrans.show(5, False)
fourTrans.write.csv("/mnt/southridge/vanarsdelltd/output/rentals.csv")

# COMMAND ----------

dbutils.fs.unmount("/mnt/southridge")

# COMMAND ----------

