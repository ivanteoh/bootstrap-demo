#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

import certifi
import codecs
import logging
import os
import urllib3


def format_description(description):
    if not description:
        return ""

    variable_description = ""
    for content in description.contents:
        if isinstance(content, basestring):
            variable_description += content
        elif content.name == "code":
            variable_description += "`" + content.string + "`"
        elif content.name == "strong":
            variable_description += "**" + content.string + "**"
        else:
            logging.warning("**Warning** " + content.name)
    return variable_description


def less_variables():
    filename = "./less/variables.less"
    raw_url = ("http://raw.githubusercontent.com/twbs/bootstrap/master/docs/"
               "_includes/customizer-variables.html")

    http = urllib3.PoolManager(
        cert_reqs="CERT_REQUIRED",  # Force certificate check.
        ca_certs=certifi.where(),   # Path to the Certifi bundle.
    )

    # You're ready to make verified HTTPS requests.
    try:
        request_content = http.request("GET", raw_url)
    except urllib3.exceptions.SSLError as e:
        # Handle incorrect certificate error.
        logging.warning("SSLError: %s" % e)
    soup = BeautifulSoup(request_content.data)
    if (len(soup.find_all("body")) != 1):
        return

    max_label_length = 0
    values = []
    headers = soup.find_all("body")[0].find_all(["h2", "h3"])
    for header in headers:
        value_dict = {}
        value_dict["name"] = header.string
        description = header.find_next_sibling("p")
        value_dict["description"] = format_description(description)
        div_row = header.find_next_sibling("div")
        value_dict["variables"] = []
        if div_row:
            labels = div_row.find_all("label")
            label_list = []
            for label in labels:
                if "for" not in label.attrs:
                    continue
                label_for = label["for"]
                label_tag = header.find_next_sibling(
                    "div").find("input", id=label_for)
                if not(label_tag):
                    continue
                if "value" not in label_tag.attrs:
                    continue
                label_paragraph = label_tag.find_next_sibling("p")
                label_description = format_description(label_paragraph)
                if len(label.string) > max_label_length:
                    max_label_length = len(label.string)
                label_list.append(dict(
                    css_label=label.string,
                    css_value=label_tag["value"],
                    css_description=label_description))
                logging.debug(header.string + " " + label.string)
            value_dict["variables"] = label_list
        values.append(value_dict)

    max_label_length += 2
    with codecs.open(filename, "w", "utf8") as outfile:
        outfile.write("// Custom" + os.linesep)
        outfile.write("// Variables" + os.linesep)
        outfile.write("// " + "-" * 50 + os.linesep + os.linesep)
        for value_dict in values:
            outfile.write(os.linesep)
            outfile.write("//== " + value_dict["name"] + os.linesep)
            outfile.write("//" + os.linesep)
            outfile.write("//##")
            if value_dict["description"]:
                outfile.write(" " + value_dict["description"] + os.linesep +
                              os.linesep)
            else:
                outfile.write(os.linesep + os.linesep)
            for variable in value_dict["variables"]:
                space_length = max_label_length - len(variable["css_label"])
                if variable["css_description"]:
                    outfile.write("//** " + variable["css_description"]
                                  + os.linesep)
                outfile.write(variable["css_label"] + ":" + " " *
                              space_length + variable["css_value"] + ";" +
                              os.linesep)
            outfile.write(os.linesep)

    return

if __name__ == "__main__":
    logging.root.setLevel(logging.WARNING)
    less_variables()
