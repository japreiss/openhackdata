# Databricks notebook source
configs = {"fs.azure.account.auth.type": "OAuth",
       "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
       "fs.azure.account.oauth2.client.id": "86642a93-7dc5-414a-86cc-3b377f8b5d7f",
       "fs.azure.account.oauth2.client.secret": "V/tHco8vmSDAjKKreCwg4ZRLdVrBVpqS9lekWuBtVeI=",
       "fs.azure.account.oauth2.client.endpoint": "https://login.microsoftonline.com/2eb86c1f-71e5-4dd8-850a-33058adc0996/oauth2/token",
       "fs.azure.createRemoteFileSystemDuringInitialization": "true"}

dbutils.fs.mount(
source = "abfss://southridge@southridgeteam7v2.dfs.core.windows.net/",
mount_point = "/mnt/southridge",
extra_configs = configs)

# COMMAND ----------

import pyspark.sql.functions as fns
from pyspark.sql.functions import col, lit

# COMMAND ----------

dbutils.fs.ls("/mnt/southridge/")

# COMMAND ----------

fourthMovies = spark.read.format('csv').options(header='true', inferschema='true').load("/mnt/southridge/fourthcoffee/rentals/movies.csv")

fourthMovies.printSchema()

# COMMAND ----------

fourthMovies.show(2,False)

# COMMAND ----------

fourthMovieActors = spark.read.format('csv').options(header='true', 
fourthMovieActors.printSchema()

# COMMAND ----------

fourthActors = spark.read.format('csv').options(header='true', inferschema='true').load("/mnt/southridge/fourthcoffee/rentals/actors.csv")

fourthActors.printSchema()

# COMMAND ----------

fourthTrans = (fourthMovies
               .join(fourthMovieActors, on="MovieID")
               .join(fourthActors, on="ActorID"))

fourthTrans = (fourthTrans
               .select(col("MovieID"),
                       col("MovieTitle"),
                       col("Category").alias("Genre"),
                       col("Rating"),
                       lit(3).alias("SourceID"),
                       fns.to_date(col("ReleaseDate"), "MM-dd-yy").alias("AvailabilityDate"),
                       fns.substring(col("ReleaseDate"), 7, 4).cast("int").alias("AvailabilityYear"),
                       fns.monotonically_increasing_id().alias("CatalogID"), 
                       "ActorID",
                       col("ActorName").alias("Actor"),
                       lit(None).cast("int").alias("MovieTier")))

fourthTrans.write.csv("/mnt/southridge/fourthcoffee/output/catalog.csv")



# COMMAND ----------

fourthCustomer = spark.read.format('csv').options(header='true', inferschema='true').load("/mnt/southridge/fourthcoffee/rentals/customers.csv")

fourthCustomer.printSchema()

# COMMAND ----------

fourthCust = (fourthCustomer.select(
  lit(3).alias("SourceID"),
  "CustomerID",
  fns.monotonically_increasing_id().cast("string").alias("AddressID"),
  "AddressLine1",
  "AddressLine2",
  "City",
  "State",
  "ZipCode",
  "CreatedDate",
  "UpdatedDate"
)).select("*",fns.concat("SourceID", "CustomerID", "AddressID").alias("UniqueID"))

fourthTrans.write.csv("/mnt/southridge/fourthcoffee/output/address.csv")

# COMMAND ----------

fourthCust = (fourthCustomer.select(
  lit(3).alias("SourceID"),
  "CustomerID",
  "LastName",
  "FirstName",
  "PhoneNumber",
  "CreatedDate",
  "UpdatedDate"
)).select("*",fns.concat("SourceID", "CustomerID").alias("UniqueID"))

fourthTrans.write.csv("/mnt/southridge/fourthcoffee/output/customer.csv")

# COMMAND ----------

fourTransactions = spark.read.format('csv').options(header='true', inferschema='true').load("/mnt/southridge/fourthcoffee/rentals/transactions.csv")

fourTransactions.show(2,False)

# COMMAND ----------

fourTransactions.select("RentalDate",
  fns.to_date(col("RentalDate").cast("string"), "yyyyMMdd").alias("RentalDate")
  ).show(2, False)


# COMMAND ----------

fourTrans = (fourTransactions.select(
  lit(3).alias("SourceID"),
  "TransactionID",
  "CustomerID",
  "MovieID",
  fns.to_date(col("RentalDate").cast("string"), "yyyyMMdd").alias("RentalDate"),
  fns.to_date(col("ReturnDate").cast("string"), "yyyyMMdd").alias("ReturnDate"),
  col("RentalCost").alias("RentalFee"),
  "LateFee",
  col("RewindFlag").cast("boolean").alias("RewindFlag"),
  "CreatedDate",
  "UpdatedDate"
)).select(
  "*",
  fns.concat("SourceID", "TransactionID").alias("UniqueOrderID"),
  fns.concat("SourceID", "CustomerID").alias("SourceCustomerID"),
fns.concat("SourceID", "MovieID").alias("SourceMovieID"))


fourTrans.write.csv("/mnt/southridge/fourthcoffee/output/rentals.csv")

# COMMAND ----------

