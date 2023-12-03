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


def run_all_corr_graphs(inputNb, scatter_x, scatter_y):
    # NYC Pluto land-use data
    data_1 = pd.read_csv(
        "/Data/pluto_nyc_landuse.csv")

    # Below grabs the ID code from above corresponding to the input neighborhood
    inputNbID = int(
        sqldf("""select distinct cd from nbLabels where nbName = '""" +
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
                                            'num_floors'])[
                               'geometry'].transform(
        'first').
                           drop_duplicates().dropna())
    bblGeom = gpd.clip(bblGeom, nbByID)
    bblGeom["bbl"] = bblGeom["bbl"].astype(int)

    # List of rezoning applications in Manhattan
    data_4 = pd.read_csv(
        '/Data/zoning_applications.csv')
    data_4 = data_4.where(data_4["validated_borough"] == "Manhattan").dropna()
    rezoningList = data_4[["project_id", "bbl"]]
    rezoningList["project_id"] = \
    rezoningList["project_id"].str.split(' - ').str[0]

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

    if (scatter_x == "medianAge"):
        disp_x = "Median age"
    elif (scatter_x == "medianIncome"):
        disp_x = "Median income ($USD)"
    elif (scatter_x == "minorityPop"):
        disp_x = "% racial minority"
    elif (scatter_x == "propMixedUseZoned"):
        disp_x = "% zoning mixed-use"
    elif (scatter_x == "propResidentialZoned"):
        disp_x = "% zoning residential"

    if (scatter_y == "medianAge"):
        disp_y = "Median age"
    elif (scatter_y == "medianIncome"):
        disp_y = "Median income ($USD)"
    elif (scatter_y == "minorityPop"):
        disp_y = "% racial minority"
    elif (scatter_y == "propMixedUseZoned"):
        disp_y = "% zoning mixed-use"
    elif (scatter_y == "propResidentialZoned"):
        disp_y = "% zoning residential"

    r, p = stats.pearsonr(np.ndarray.
                          flatten(censusTractsReg[scatter_y].values.reshape(-1, 1)),
                          np.ndarray.flatten(
                              censusTractsReg[scatter_x].values.reshape(-1, 1)))
    r = np.round(r, 2)
    p = np.round(p, 2)

    ax6 = plt.axes()
    ax6.scatter(censusTractsReg[scatter_x], censusTractsReg[scatter_y], c="black",
            s=2)

    try:
        a, b = np.polyfit(censusTractsReg[scatter_x],
                          censusTractsReg[scatter_y], 1)
        ax6.plot(censusTractsReg[scatter_x], a * censusTractsReg[scatter_x] + b,
                 c="red", linewidth=1)
    except:
        ax6.plot(censusTractsReg[scatter_x], 0 * censusTractsReg[scatter_x] + 0,
                 c="black", linewidth=0)

    plt.xlabel(disp_x, fontsize=12)
    plt.ylabel(disp_y, fontsize=12)
    plt.text(0.27, 3.1, "r=" + str(r) +", p="+str(p), fontsize=12, transform=ax6.transAxes)

    plt.savefig(
        "/Graphics/2023_scatter_" +
        inputNb.replace(" ", "_").replace("/", "_") +
        "_" + scatter_x + "_" + scatter_y, dpi=300)

    plt.clf()

# Plot scatters of variable correlations for the nb in question
# median age vs. median income
# % minority vs. median age
# % minority vs. median income
# % mixed use vs. % minority
# % residential vs. median age
# % residential vs. median income
# % residential vs. % minority

for i in np.array(nbLabels["nbName"]):
    run_all_corr_graphs(i, "medianAge", "medianIncome")
    run_all_corr_graphs(i, "minorityPop", "medianAge")
    run_all_corr_graphs(i, "minorityPop", "medianIncome")
    run_all_corr_graphs(i, "propMixedUseZoned", "minorityPop")
    run_all_corr_graphs(i, "propResidentialZoned", "medianAge")
    run_all_corr_graphs(i, "propResidentialZoned", "medianIncome")
    run_all_corr_graphs(i, "propResidentialZoned", "minorityPop")
