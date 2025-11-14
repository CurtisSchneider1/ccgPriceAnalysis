import pandas as pd

dfm = pd.read_csv('../data/dataMagic/cardsMagic.csv') # 8/26/25

# Specify the needed columns
dfm = dfm[["availability", "colors", "language", "name", "rarity", "setCode", "types", "uuid"]]

# Replace all NaN with "C" for "Colorless"
dfm["colors"] = dfm["colors"].fillna("C")

# Specifying the rows to keep involving paper
dfm = dfm[
    (dfm["availability"] == "mtgo, paper") | 
    (dfm["availability"] == "paper") | 
    (dfm["availability"] == "arena, mtgo, paper") |
    (dfm["availability"] == "arena, paper") 
    ]

# Only want the English card versions
dfm = dfm[dfm["language"] == "English"]

# We're also going to remove the basic lands from each set.  
# These lands are printed every set in bulk and are mostly worthless, barring certain outliers.  
# This will tighten our dataset and focus it toward value.  
basic_lands = ["Forest", "Island", "Mountain", "Plains", "Swamp"]
dfm = dfm[~dfm["name"].isin(basic_lands)]

dfmSets = pd.read_csv('../data/dataMagic/setsMagic.csv') # 9/22/25

dfm2 = pd.merge(dfm, dfmSets, on = "setCode", how = "inner")

dfmPrices =  pd.read_csv('../data/dataMagic/pricesMagic.csv') # 8/27/25

mtgo = ["mtgo"]
buylist = ["buylist"]
cardmarket = ["cardmarket"]
dfmPrices = dfmPrices[~dfmPrices["gameAvailability"].isin(mtgo)]
dfmPrices = dfmPrices[~dfmPrices["providerListing"].isin(buylist)]
dfmPrices = dfmPrices[~dfmPrices["priceProvider"].isin(cardmarket)]

dfm3 = pd.merge(dfm2, dfmPrices, on = "uuid", how = "left")

dfm3["avgMarketPrice"] = dfm3.groupby(['uuid', 'cardFinish'])['price'].transform('mean')

dfm3["avgMarketPrice"] = dfm3["avgMarketPrice"].round(2)

dfm3.drop(columns = ["availability"], inplace = True)

dfm3['releaseDate'] = pd.to_datetime(dfm3['releaseDate'], format = '%m/%d/%Y', errors = 'raise')

# A more viewer-friendly order
newOrderM = ['name', 'setCode', 'setName', 'language', 'types', 'colors', 'rarity', 'cardFinish', 'releaseDate', 'releaseYear', 'gameAvailability', 
             'priceProvider', 'price', 'avgMarketPrice', 'currency', 'providerListing', 'date', 'uuid']
dfm3 = dfm3[newOrderM]

# Order by year, then setName, then name
dfm3 = dfm3.sort_values(by=["releaseDate", "setName", "name"])

# Reset index after manipulation and to check new number of rows
# Dropping the original index column
dfm3 = dfm3.reset_index(drop = True)

# dfm3 will be used for SQL queries and individual price lookups
# dfm4 will be used for visualization, based on avgMarketPrice, and will be cleaner with less indexes based on UUID
dfm4 = dfm3.drop(columns = ["price", "priceProvider"])

dfm4.drop_duplicates(keep = "first", inplace = True)

# Reset index again
dfm4 = dfm4.reset_index(drop = True)



# Visualization Prep

setValueMagic = dfm4.groupby("setName").agg({
    "avgMarketPrice" : "sum",
    "releaseYear" : "first"
})
# reset index so setName and releaseYear are columns
setValueMagicClean = setValueMagic.reset_index()
# ordering
setValueMagicClean = setValueMagicClean.sort_values(by=["releaseYear", "avgMarketPrice"], ascending = False)
# outputting
setValueMagicClean.to_csv("../data/dataMagic/setValueMagicClean.csv", index = False)


# To show the top sets from each year for graph ax text
setSumMagic = dfm4.groupby(["releaseYear", "setName"], as_index=False)["avgMarketPrice"].sum()
# For each year, the set with the highest total price
topSetsMagic = setSumMagic.loc[setSumMagic.groupby("releaseYear")["avgMarketPrice"].idxmax()]
topSetsMagic = topSetsMagic.sort_values("avgMarketPrice").round()
topSetsMagic = topSetsMagic.sort_values("releaseYear")