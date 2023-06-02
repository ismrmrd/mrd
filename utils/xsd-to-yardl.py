
import argparse
import xmlschema
from typing import List, Dict
from io import StringIO
import string

def to_pascal_case(s: str):
    temp = s.split('_')
    res = temp[0] + ''.join(ele.title() for ele in temp[1:])
    res = res[0].upper() + res[1:]
    return res

def to_camel_case(s: str):
    temp = s.split('_')
    res = temp[0] + ''.join(ele.title() for ele in temp[1:])
    res = res[0].lower() + res[1:]
    return res

def render_enum(field: xmlschema.XsdElement, records: Dict[str, str] = {}):
    outp = StringIO()
    outp.write(to_pascal_case(field.local_name) + ": !enum\n")
    outp.write("  " +  "  values:\n")
    if field.type.enumeration is not None:
        res: List = field.type.enumeration
        for enum in res:
            outp.write("    - " + to_camel_case(enum) + "\n")
    elif field.type.patterns is not None:
        # We only have one of those, gender
        outp.write("    - m\n")
        outp.write("    - f\n")
        outp.write("    - o\n")

    records[to_pascal_case(field.local_name)] = outp.getvalue()

def render_record(element: xmlschema.XsdElement, records: Dict[str, str] = {}):
    outp = StringIO()
    if element.type.local_name is None:
        raise Exception("Element has no type: " + str(element))
    outp.write(to_pascal_case(element.type.local_name) + ": !record\n")
    outp.write("  fields:\n")
    for field in element:
        is_optional = "?" if field.min_occurs == 0 else ""

        if field.max_occurs is None or field.max_occurs > 1:
            is_optional = "*"

        if field.type.is_complex():
            if to_pascal_case(field.type.local_name) not in records:
                render_record(field, records)

            outp.write("    " + to_camel_case(field.local_name) + ": " + to_pascal_case(field.type.local_name) + is_optional + "\n")
        elif field.type.is_atomic() and not field.type.is_restriction():
            if field.type.local_name == "long":
                outp.write("    " +  to_camel_case(field.local_name) + ": long" + is_optional + "\n")
            elif field.type.local_name == "unsignedShort":
                outp.write("    " +  to_camel_case(field.local_name) + ": uint" + is_optional + "\n")
            elif field.type.local_name == "unsignedInt":
                outp.write("    " +  to_camel_case(field.local_name) + ": uint" + is_optional + "\n")
            elif field.type.local_name == "unsignedLong":
                outp.write("    " +  to_camel_case(field.local_name) + ": uint64" + is_optional + "\n")
            elif field.type.local_name == "float":
                outp.write("    " +  to_camel_case(field.local_name) + ": float" + is_optional + "\n")
            elif field.type.local_name == "double":
                outp.write("    " +  to_camel_case(field.local_name) + ": double" + is_optional + "\n")
            elif field.type.local_name == "string":
                outp.write("    " +  to_camel_case(field.local_name) + ": string" + is_optional + "\n")
            elif field.type.local_name == "date":
                outp.write("    " +  to_camel_case(field.local_name) + ": date" + is_optional + "\n")
            elif field.type.local_name == "time":
                outp.write("    " +  to_camel_case(field.local_name) + ": time" + is_optional + "\n")
            elif field.type.local_name == "base64Binary":
                outp.write("    " +  to_camel_case(field.local_name) + ": string" + is_optional + "\n")
            else:
                raise Exception("Unknown type: " + str(field.type))
        elif field.type.is_atomic() and field.type.is_restriction():
            if to_pascal_case(to_pascal_case(field.local_name)) not in records:
                render_enum(field, records)
            outp.write("    " +  to_camel_case(field.local_name) + ": " + to_pascal_case(field.local_name) + is_optional + "\n")
        else:
            raise Exception("Unknown type: " + str(field.type))

    records[str(element.type.local_name)] = outp.getvalue()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Converts an XSD to a YARDL file.")
    parser.add_argument("xsd", help="The XSD file to convert.")
    args = parser.parse_args()

    records = {}
    schema = xmlschema.XMLSchema(args.xsd)

    for element in schema:
        render_record(element, records)

    for key in records:
        print(records[key].replace("IsmrmrdHeader", "Header"))
