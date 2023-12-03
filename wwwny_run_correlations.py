import pandas as pd
from pandasql import sqldf
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import warnings
import matplotlib
from scipy import stats

plt.rcParams["font.family"] = "Avenir"
matplotlib.rcParams['figure.dpi'] = 100

warnings.filterwarnings('ignore')

##############################
# Input neighborhood
inputNb = "Inwood"
##############################

# Static calls
data_1 = pd.read_csv(
    "/Data/pluto_nyc_landuse.csv")

# Readable neighborhood/CD names
nbLabels = pd.DataFrame(np.array(
    [[101, "Tribeca/Battery Park", 977500, 986100, 193500, 204500],
     [102, "SoHo/West Village", 979150, 988350, 199700, 210200],
     [103, "Chinatown/LES", 983500, 992500, 196800, 207400],
     [104, "Chelsea/Hudson Yards", 980200, 990300, 206900, 222000],
     [105, "Flatiron/Midtown", 983500, 994500, 205500, 220000],
     [106, "Turtle Bay", 986200, 996500, 205000, 217500],
     [107, "UWS", 985500, 996900, 218500, 233200],
     [108, "UES", 990600, 1001700, 214000, 227500],
     [109, "West Harlem", 991900, 1001500, 230500, 243900],
     [110, "Central Harlem", 994000, 1004000, 228500, 244800],
     [111, "East Harlem", 995500, 1008500, 223000, 238000],
     [112, "Inwood", 995500, 1010000, 240000, 260000]]),
    columns=['cd', 'nbName', 'xmin', 'xmax', 'ymin',
             'ymax'])  # add plot bounding box
nbLabels["cd"] = nbLabels["cd"].astype(int)

# Full script call
# Below grabs the ID code from above corresponding to the input neighborhood
inputNbID = int(sqldf("""select distinct cd from nbLabels where nbName = '""" +
                      inputNb + "'").squeeze())

# Below grabs the bounding box from the input neighborhood
xRangeMin = int(
    sqldf("""select distinct xmin from nbLabels where nbName = '""" +
          inputNb + "'").squeeze())
xRangeMax = int(
    sqldf("""select distinct xmax from nbLabels where nbName = '""" +
          inputNb + "'").squeeze())
yRangeMin = int(
    sqldf("""select distinct ymin from nbLabels where nbName = '""" +
          inputNb + "'").squeeze())
yRangeMax = int(
    sqldf("""select distinct ymax from nbLabels where nbName = '""" +
          inputNb + "'").squeeze())

# Cleaned boundary of the chosen neighborhood's geometry
data_2 = gpd.read_file(
    "/Data/nyc_nb.shp")
nbByID = data_2.where(data_2["boro_cd"] == inputNbID)

# Clipped bbl geometry based on neighborhood geometry
data_3 = gpd.read_file(
    "/Data/nycbbl.shp",
    mask=nbByID)
bblGeom = data_3[["bbl", "num_floors", "geometry"]]

# There are some duplicate bbl entries, so we'll grab the first
# parcel per bbl as an approximation
bblGeom["geometry"] = (bblGeom.groupby(['bbl',
                                        'num_floors'])['geometry'].transform(
    'first').
                       drop_duplicates().dropna())
bblGeom = gpd.clip(bblGeom, nbByID)
bblGeom["bbl"] = bblGeom["bbl"].astype(int)

# List of rezoning applications in Manhattan
data_4 = pd.read_csv(
    '/Data/zoning_applications.csv')
data_4 = data_4.where(data_4["validated_borough"] == "Manhattan").dropna()
rezoningList = data_4[["project_id", "bbl"]]
rezoningList["project_id"] = rezoningList["project_id"].str.split(' - ').str[0]

# Add metadata and information to rezoning applications from detailed dataset
data_5 = pd.read_csv(
    '/Data/zoning_applications_2.csv')
rezoningList = rezoningList.merge(data_5, on="project_id", how="inner")
rezoningList = rezoningList[
    ["project_id", "bbl", "project_name", "project_status",
     "actions"]]

# Add ACS census data for demographic attributes
data_6 = pd.read_csv(
    '/Data/acs_census_data.csv')
data_6 = data_6.iloc[1:, :]
acsCensus = data_6[["GEO_ID"]]  # drop first row as it's attributes
acsCensus = acsCensus.rename(columns={"GEO_ID": "GEOID"})
acsCensus["GEOID"] = acsCensus["GEOID"].str[9:]
acsCensus["totalPop"] = data_6["S0601_C01_001E"]
acsCensus["medianAge"] = data_6["S0601_C01_010E"]
acsCensus["whitePop"] = data_6["S0601_C01_014E"]
acsCensus["medianIncome"] = data_6["S0601_C01_047E"]

# Now, add the census tract shapefile
data_7 = gpd.read_file(
    '/Data/tl_2018_36_tract.shp')
censusTracts = data_7[["GEOID", "geometry"]]
censusTracts = gpd.clip(censusTracts, nbByID)
censusTracts = censusTracts.merge(acsCensus, on="GEOID", how="inner")
censusTracts = censusTracts.where(censusTracts["whitePop"] != "-")
censusTracts = censusTracts.where(censusTracts["medianIncome"] != "-")
censusTracts["minorityPop"] = censusTracts["whitePop"].astype(float) * (
    -1) + 100
censusTracts = censusTracts.drop(columns=['whitePop'])

# Join our datasets
NbLandUse = data_1.merge(bblGeom, on="bbl", how="inner")
NbLandUse = NbLandUse.merge(nbLabels, on="cd", how="inner")

# Get simple zoning typologies for creating a mixed use flag
NbLandUse["zd1tp"] = NbLandUse["zonedist1"].astype(str).str[0]
NbLandUse["zd2tp"] = NbLandUse["zonedist2"].astype(str).str[0]
NbLandUse["zd3tp"] = NbLandUse["zonedist3"].astype(str).str[0]
NbLandUse["zd4tp"] = NbLandUse["zonedist4"].astype(str).str[0]

# Create mixed use flag by looking through permutations
NbLandUse["zoningtp"] = np.where(((NbLandUse["zonedist1"] != NbLandUse[
    "zonedist2"]) & (~(NbLandUse["zonedist2"].isna()))) | ((NbLandUse[
                                                                "zonedist1"] !=
                                                            NbLandUse[
                                                                "zonedist3"]) & (
                                                               ~(NbLandUse[
                                                                     "zonedist3"].isna()))) | (
                                             (NbLandUse["zonedist1"] !=
                                              NbLandUse[
                                                  "zonedist4"]) & (~(
                                         NbLandUse["zonedist4"].isna()))),
                                 "Mixed", "Single")
NbLandUse["primaryzoning"] = np.where(NbLandUse["zoningtp"] == "Mixed",
                                      "MX", NbLandUse["zd1tp"])
landUseLabels = pd.DataFrame(np.array(
    [["C", "Commercial"], ["M", "Manufacturing"],
     ["MX", "Mixed-use"], ["P", "Park"],
     ["R", "Residential"]]),
    columns=['primaryzoning', 'landusereadable'])
NbLandUse = NbLandUse.merge(landUseLabels, on="primaryzoning", how="inner")

# left join in the rezoning applications
NbLandUse = NbLandUse.merge(rezoningList, on="bbl", how="left")
NbLandUse = NbLandUse[
    ["bbl", "nbName", "landusereadable", "primaryzoning", "zoningtp",
     "project_id",
     "project_name", "project_status",
     "actions",
     "numfloors", "unitstotal", "lottype", "yearbuilt",
     "block", "lot", "cd", "zipcode",
     "address", "lotarea", "zd1tp", "zonedist1", "zonedist2", "zonedist3",
     "zonedist4",
     "geometry"]]
NbLandUse = gpd.GeoDataFrame(NbLandUse)

# Let's find the intersection of bbl geometries within or crossing the border of any
# census tracts, then, count the number of each type of land use within
censusTracts = censusTracts.to_crs("epsg:2263")
NbLandUse = NbLandUse.to_crs("epsg:2263")
joinedTractsDemos = NbLandUse.sjoin(censusTracts, how="inner")
joinedTractsDemos = joinedTractsDemos[
    ["GEOID", "totalPop", "medianAge", "medianIncome",
     "minorityPop", "primaryzoning"]]
joinedTractsDemos = sqldf("""select distinct GEOID, 
totalPop, 
cast(medianAge as float) as medianAge, 
cast(medianIncome as float) as medianIncome,
 cast(minorityPop as float) as minorityPop,
cast(residentialZoned as float)/
cast(residentialZoned + otherZoned + mixedUseZoned as float) *100
as propResidentialZoned,
cast(otherZoned as float)/
cast(residentialZoned + otherZoned + mixedUseZoned as float) *100
as propOtherZoned,
cast(mixedUseZoned as float)/
cast(residentialZoned + otherZoned + mixedUseZoned as float) *100
as propMixedUseZoned,
 residentialZoned, otherZoned, mixedUseZoned from (
select GEOID, totalPop, medianAge, medianIncome, minorityPop,
sum(case when primaryzoning = 'R' then 1 else 0 end) as residentialZoned, 
sum(case when primaryzoning in ('P', 'M', 'C') then 1 else 0 end) as otherZoned,
sum(case when primaryzoning = 'MX' then 1 else 0 end) as mixedUseZoned
from joinedTractsDemos group by GEOID, totalPop, medianAge, medianIncome, minorityPop)""")

# Below, we get a clean final dataset with all of our variables
censusTractsReg = joinedTractsDemos[["GEOID", "totalPop", "medianAge",
                                     "medianIncome", "minorityPop",
                                     "propMixedUseZoned",
                                     "propResidentialZoned"]]

# Now, check out Pearson's correlation for an easily
# interpretable measure of relationship between variables
XminorityPop = censusTractsReg["minorityPop"]
XmedianAge = censusTractsReg["medianAge"]
XmedianIncome = censusTractsReg["medianIncome"]
YMixedUseZoned = censusTractsReg["propMixedUseZoned"]
YResidentialZoned = censusTractsReg["propResidentialZoned"]
XminorityPop = XminorityPop.values.reshape(-1, 1)
XmedianAge = XmedianAge.values.reshape(-1, 1)
XmedianIncome = XmedianIncome.values.reshape(-1, 1)
YMixedUseZoned = YMixedUseZoned.values.reshape(-1, 1)
YResidentialZoned = YResidentialZoned.values.reshape(-1, 1)

rResMinority, pResMinority = stats.pearsonr(np.ndarray.
                                            flatten(XminorityPop),
                                            np.ndarray.flatten(
                                                YResidentialZoned))
rResIncome, pResIncome = stats.pearsonr(np.ndarray.
                                        flatten(XmedianIncome),
                                        np.ndarray.flatten(YResidentialZoned))
rResAge, pResAge = stats.pearsonr(np.ndarray.
                                  flatten(XmedianAge),
                                  np.ndarray.flatten(YResidentialZoned))
rMUMinority, pMUMinority = stats.pearsonr(np.ndarray.
                                          flatten(XminorityPop),
                                          np.ndarray.flatten(YMixedUseZoned))
rMUIncome, pMUIncome = stats.pearsonr(np.ndarray.
                                      flatten(XmedianIncome),
                                      np.ndarray.flatten(YMixedUseZoned))
rMUAge, pMUAge = stats.pearsonr(np.ndarray.
                                flatten(XmedianAge),
                                np.ndarray.flatten(YMixedUseZoned))
rMinorityAge, pMinorityAge = stats.pearsonr(np.ndarray.
                                            flatten(XminorityPop),
                                            np.ndarray.flatten(XmedianAge))
rMinorityIncome, pMinorityIncome = stats.pearsonr(np.ndarray.
                                                  flatten(XmedianIncome),
                                                  np.ndarray.flatten(
                                                      XminorityPop))
rIncomeAge, pIncomeAge = stats.pearsonr(np.ndarray.
                                        flatten(XmedianIncome),
                                        np.ndarray.flatten(XmedianAge))

print("Strength of correlation between % population minority & res land use: " +
      str(rResMinority) + "\n" + "p-value: " + str(pResMinority))
print("Strength of correlation between median age & res land use: " +
      str(rResAge) + "\n" + "p-value: " + str(pResAge))
print("Strength of correlation between median income & res land use: " +
      str(rResIncome) + "\n" + "p-value: " + str(pResIncome))
print(
    "Strength of correlation between % population minority & mixed land use: " +
    str(rMUMinority) + "\n" + "p-value: " + str(pMUMinority))
print("Strength of correlation between median age & mixed land use: " +
      str(rMUAge) + "\n" + "p-value: " + str(pMUAge))
print("Strength of correlation between median income & mixed land use: " +
      str(rMUIncome) + "\n" + "p-value: " + str(pMUIncome))
print("Strength of correlation between % population minority & median age: " +
      str(rMinorityAge) + "\n" + "p-value: " + str(pMinorityAge))
print(
    "Strength of correlation between % population minority & median income: " +
    str(rMinorityIncome) + "\n" + "p-value: " + str(pMinorityIncome))
print("Strength of correlation between median income & median age: " +
      str(rIncomeAge) + "\n" + "p-value: " + str(pIncomeAge))
