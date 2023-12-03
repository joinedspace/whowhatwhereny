import pandas as pd
from pandasql import sqldf
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import warnings
import matplotlib
from matplotlib.colors import ListedColormap
from matplotlib_scalebar.scalebar import ScaleBar
import contextily as cx

plt.rcParams["font.family"] = "Avenir"
matplotlib.rcParams['figure.dpi'] = 100

warnings.filterwarnings('ignore')

##############################
# Input neighborhood
inputNb = "UWS"
##############################

# Static calls
data_1 = pd.read_csv(
    "/Data/pluto_nyc_landuse.csv")

# Readable neighborhood/CD names
nbLabels = pd.DataFrame(np.array(
    [[101, "Tribeca/Battery Park", 977500, 986100, 193500, 204500],
     [102, "SoHo/West Village", 978850, 988050, 199700, 210200],
     [103, "Chinatown/LES", 983500, 992500, 196800, 207400],
     [104, "Chelsea/Hudson Yards", 980200, 990300, 206900, 222000],
     [105, "Flatiron/Midtown", 983500, 994500, 205500, 220000],
     [106, "Turtle Bay", 986200, 996500, 203000, 217500],
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

## Plotting land-use
# An initial exploration plot with a standard land-use color scheme
plotColors = ListedColormap(["tomato", "lightskyblue", "slateblue",
                             "seagreen", "goldenrod"])
NbLandUsePlot = NbLandUse
NbLandUsePlot = NbLandUsePlot.to_crs("epsg:2263")

ax = NbLandUsePlot.plot(column="landusereadable", categorical=True,
                        legend=True,
                        legend_kwds={'loc': "upper left",
                                     'fontsize': 7,
                                     'markerscale': 0.8,
                                     'handletextpad': 0.1,
                                     'frameon': False}, cmap=plotColors)
ax.text(x=(xRangeMax - xRangeMin) / 36 + xRangeMin,
        y=(yRangeMax - yRangeMin) / 34.333 +
          yRangeMin, s="Source: OpenStreetMap, CARTO", fontsize=6)
ax.text(x=xRangeMax - (xRangeMax - xRangeMin) / 12,
        y=(yRangeMax - yRangeMin) / 34.333 +
          yRangeMin, s='N', fontsize=12)
ax.arrow(xRangeMax - (xRangeMax - xRangeMin) / 16.4336,
         (yRangeMax - yRangeMin) / 12.875 + yRangeMin, 0,
         (yRangeMax - yRangeMin) / 51.5, length_includes_head=False,
         head_width=(xRangeMax - xRangeMin) / 90,
         head_length=(yRangeMax - yRangeMin) / 103, overhang=.1,
         facecolor='black')
plt.xticks([])
plt.yticks([])

ax.add_artist(
    ScaleBar(1, dimension="imperial-length", units="ft", fixed_units="mi",
             fixed_value=0.25, box_alpha=0))
ax.set_xlim(xRangeMin, xRangeMax)
ax.set_ylim(yRangeMin, yRangeMax)
cx.add_basemap(ax, crs=NbLandUsePlot.crs,
               source=cx.providers.CartoDB.PositronNoLabels,
               attribution=False)

plt.savefig(
    "/Graphics/2023_land_use_" + inputNb.replace(
        " ", "_").replace("/", "_"), dpi=500)

## Plotting choropleths
# Plot a choropleth of median income across neighborhood census tracts
censusTracts["medianIncome"] = censusTracts["medianIncome"].dropna().astype(int)
censusTracts = censusTracts.to_crs("epsg:2263")
ax2 = censusTracts.plot(column='medianIncome', legend=True,
                        cmap='Greens',
                        alpha=1)

# Plot bounds
censusTracts = censusTracts.to_crs("epsg:2263")
censusTracts.plot(ax=ax2, facecolor="none", edgecolor="black", linewidth=0.75)

ax2.text(x=(xRangeMax - xRangeMin) / 36 + xRangeMin,
         y=(yRangeMax - yRangeMin) / 34.333 +
           yRangeMin, s="Source: OpenStreetMap, CARTO", fontsize=6)
ax2.text(x=xRangeMax - (xRangeMax - xRangeMin) / 12,
         y=(yRangeMax - yRangeMin) / 34.333 +
           yRangeMin, s='N', fontsize=12)
ax2.arrow(xRangeMax - (xRangeMax - xRangeMin) / 16.4336,
          (yRangeMax - yRangeMin) / 12.875 + yRangeMin, 0,
          (yRangeMax - yRangeMin) / 51.5, length_includes_head=False,
          head_width=(xRangeMax - xRangeMin) / 90,
          head_length=(yRangeMax - yRangeMin) / 103, overhang=.1,
          facecolor='black')
plt.xticks([])
plt.yticks([])

ax2.add_artist(
    ScaleBar(1, dimension="imperial-length", units="ft", fixed_units="mi",
             fixed_value=0.25, box_alpha=0))
ax2.set_xlim(xRangeMin, xRangeMax)
ax2.set_ylim(yRangeMin, yRangeMax)
cx.add_basemap(ax2, crs=censusTracts.crs,
               source=cx.providers.CartoDB.PositronNoLabels,
               attribution=False)

plt.savefig(
    "/Graphics/2023_median_income_" + inputNb.replace(
        " ", "_").replace("/", "_"), dpi=500)

# Plot a choropleth of median income across neighborhood census tracts
censusTracts["medianAge"] = censusTracts["medianAge"].astype(float)
censusTracts = censusTracts.to_crs("epsg:2263")
ax3 = censusTracts.plot(column='medianAge', legend=True,
                        cmap='Blues',
                        alpha=1)

# Plot bounds
censusTracts = censusTracts.to_crs("epsg:2263")
censusTracts.plot(ax=ax3, facecolor="none", edgecolor="black", linewidth=0.75)

ax3.text(x=(xRangeMax - xRangeMin) / 36 + xRangeMin,
         y=(yRangeMax - yRangeMin) / 34.333 +
           yRangeMin, s="Source: OpenStreetMap, CARTO", fontsize=6)
ax3.text(x=xRangeMax - (xRangeMax - xRangeMin) / 12,
         y=(yRangeMax - yRangeMin) / 34.333 +
           yRangeMin, s='N', fontsize=12)
ax3.arrow(xRangeMax - (xRangeMax - xRangeMin) / 16.4336,
          (yRangeMax - yRangeMin) / 12.875 + yRangeMin, 0,
          (yRangeMax - yRangeMin) / 51.5, length_includes_head=False,
          head_width=(xRangeMax - xRangeMin) / 90,
          head_length=(yRangeMax - yRangeMin) / 103, overhang=.1,
          facecolor='black')

plt.xticks([])
plt.yticks([])

ax3.add_artist(
    ScaleBar(1, dimension="imperial-length", units="ft", fixed_units="mi",
             fixed_value=0.25, box_alpha=0))
ax3.set_xlim(xRangeMin, xRangeMax)
ax3.set_ylim(yRangeMin, yRangeMax)
cx.add_basemap(ax3, crs=censusTracts.crs,
               source=cx.providers.CartoDB.PositronNoLabels,
               attribution=False)

plt.savefig(
    "/Graphics/2023_median_age_" + inputNb.replace(
        " ", "_").replace("/", "_"), dpi=500)

# Plot a choropleth of median income across neighborhood census tracts
censusTracts["minorityPop"] = censusTracts["minorityPop"].astype(float)
censusTracts = censusTracts.to_crs("epsg:2263")
ax4 = censusTracts.plot(column='minorityPop', legend=True,
                        cmap='Purples',
                        alpha=1)

# Plot bounds
censusTracts = censusTracts.to_crs("epsg:2263")
censusTracts.plot(ax=ax4, facecolor="none", edgecolor="black", linewidth=0.75)

ax4.text(x=(xRangeMax - xRangeMin) / 36 + xRangeMin,
         y=(yRangeMax - yRangeMin) / 34.333 +
           yRangeMin, s="Source: OpenStreetMap, CARTO", fontsize=6)
ax4.text(x=xRangeMax - (xRangeMax - xRangeMin) / 12,
         y=(yRangeMax - yRangeMin) / 34.333 +
           yRangeMin, s='N', fontsize=12)
ax4.arrow(xRangeMax - (xRangeMax - xRangeMin) / 16.4336,
          (yRangeMax - yRangeMin) / 12.875 + yRangeMin, 0,
          (yRangeMax - yRangeMin) / 51.5, length_includes_head=False,
          head_width=(xRangeMax - xRangeMin) / 90,
          head_length=(yRangeMax - yRangeMin) / 103, overhang=.1,
          facecolor='black')
plt.xticks([])
plt.yticks([])

ax4.add_artist(
    ScaleBar(1, dimension="imperial-length", units="ft", fixed_units="mi",
             fixed_value=0.25, box_alpha=0))
ax4.set_xlim(xRangeMin, xRangeMax)
ax4.set_ylim(yRangeMin, yRangeMax)
cx.add_basemap(ax4, crs=censusTracts.crs,
               source=cx.providers.CartoDB.PositronNoLabels,
               attribution=False)

plt.savefig(
    "/Graphics/2023_minority_pop_" + inputNb.replace(
        " ", "_").replace("/", "_"), dpi=500)
