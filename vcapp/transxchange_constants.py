ALL_BLUE_MOUNTAINS_SERVICES = range(9833, 9848)
INBOUND_BLUE_MOUNTAINS_SERVICES = (9833, 9835, 9838, 9840, 9841, 9843, 9844,
                                   9847)
YELLOW_LINE_SERVICES = [9901, 9903, 9904, 9906, 9908, 9909, 9911, 9964, 9965,
                        9966, 9967, 9968, 9969, 9972, 9973, 9974]
# 9847 has a hornsby to springwood service thrown in for good measure :-(
#INBOUND_BLUE_MOUNTAINS_SERVICES = (9833, 9835, 9838, 9840, 9841, 9843, 9844)
TEST_SERVICES = (9843,)

#SERVICE_LIST = YELLOW_LINE_SERVICES + ALL_BLUE_MOUNTAINS_SERVICES
#SERVICE_LIST = ALL_BLUE_MOUNTAINS_SERVICES

LITHGOW_TO_CENTRAL_ORIGINS = ("Lithgow Station",
                              "Mount Victoria Station",
                              "Katoomba Station",
                              "Springwood Station")
CENTRAL_TO_LITHGOW_ORIGINS = ("Central Station", "Hornsby Station",)
PENRITH_TO_HORNSBY_ORIGINS = ("Emu Plains Station",
                              "Penrith Station",
                              "Richmond Station",
                              "Blacktown Station",
                              "Quakers Hill Station")
HORNSBY_TO_PENRITH_ORIGINS = ("Berowra Station",
                              "Hornsby Station",
                              "Gordon Station",
                              "North Sydney Station",
                              "Wyong Station",
                              "Lindfield Station")

INTERCHANGE_LINE_NAME = "Dummy Interchange Line"
LINE_NAMES = ["Blue Mountains - Lithgow to Central",
              "Blue Mountains - Central to Lithgow",
              "Western Line - Penrif to Hornsby",
              "Western Line - Hornsby to Penrif",
              ]

# List the stations that are on each line
# TODO: Generate this automatically?
INTERCHANGE_STATION_MAP = {
    "Emu Plains Station": (1, 2, 3, 4),
    "Penrith Station": (1, 2, 3, 4),
    "Blacktown Station": (1, 2, 3, 4),
    "Westmead Station": (1, 2, 3, 4),
    "Parramatta Station": (1, 2, 3, 4),
    "Granville Station": (1, 2, 3, 4),
    "Lidcombe Station": (1, 2, 3, 4),
    "Strathfield Station": (1, 2, 3, 4),
    "Burwood Station": (3, 4),
    "Redfern Station": (1, 2, 3, 4),
    "Central Station": (1, 2, 3, 4),
    "Town Hall Station": (3, 4),
    "Wynyard Station": (3, 4),
    "North Sydney Station": (3, 4)
}
