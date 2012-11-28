import math

def line_magnitude (x1, y1, x2, y2):
    return math.sqrt(math.pow((x2 - x1), 2) + math.pow((y2 - y1), 2))

#Calc minimum distance from a point and a line segment (i.e. consecutive vertices in a polyline).
def distance_point_line (px, py, x1, y1, x2, y2):
    #http://local.wasp.uwa.edu.au/~pbourke/geometry/pointline/source.vba
    LineMag = line_magnitude(x1, y1, x2, y2)

    if LineMag < 0.00000001:
        dpl = 9999
        return dpl

    u1 = (((px - x1) * (x2 - x1)) + ((py - y1) * (y2 - y1)))
    u = u1 / (LineMag * LineMag)

    if (u < 0.00001) or (u > 1):
        #// closest point does not fall within the line segment, take the shorter distance
        #// to an endpoint
        ix = line_magnitude(px, py, x1, y1)
        iy = line_magnitude(px, py, x2, y2)
        if ix > iy:
            dpl = iy
        else:
            dpl = ix
    else:
        # Intersecting point is on the line, use the formula
        ix = x1 + u * (x2 - x1)
        iy = y1 + u * (y2 - y1)
        dpl = line_magnitude(px, py, ix, iy)

    return dpl
