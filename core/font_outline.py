"""
SVG Path d-attribute serializer for QPainterPath.
Converts Qt bezier curves and lines into standard SVG path syntax.
"""

from PySide6.QtGui import QPainterPath


def painter_path_to_svg_d(path: QPainterPath, offset_x=0.0, offset_y=0.0) -> str:
    """Convert QPainterPath to standard SVG 'd' string with optional translation."""
    d_parts = []
    count = path.elementCount()
    i = 0

    while i < count:
        elem = path.elementAt(i)
        elem_type = elem.type

        # MoveTo
        if elem_type == QPainterPath.ElementType.MoveToElement:
            x = elem.x + offset_x
            y = elem.y + offset_y
            d_parts.append(f"M {x:.2f} {y:.2f}")
            i += 1

        # LineTo
        elif elem_type == QPainterPath.ElementType.LineToElement:
            x = elem.x + offset_x
            y = elem.y + offset_y
            d_parts.append(f"L {x:.2f} {y:.2f}")
            i += 1

        # CurveTo
        elif elem_type == QPainterPath.ElementType.CurveToElement:
            # CurveTo element is followed by CurveToDataElement (control 2 and end point)
            cp1_x = elem.x + offset_x
            cp1_y = elem.y + offset_y

            i += 1
            if i < count:
                cp2 = path.elementAt(i)
                cp2_x = cp2.x + offset_x
                cp2_y = cp2.y + offset_y
            else:
                break

            i += 1
            if i < count:
                end_p = path.elementAt(i)
                end_x = end_p.x + offset_x
                end_y = end_p.y + offset_y
            else:
                break

            d_parts.append(f"C {cp1_x:.2f} {cp1_y:.2f}, {cp2_x:.2f} {cp2_y:.2f}, {end_x:.2f} {end_y:.2f}")
            i += 1

        else:
            i += 1

    return " ".join(d_parts) + " Z" if d_parts else ""
