'''
Copyright 2020 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Aug 07 2020
File : report_artifacts.py
'''

import logging
import os
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

#--------------------------------------------------------------------------------#
def create_report_artifacts(reportData):
    logger.info("Entering create_report_artifacts")

    # Dict to hold the complete list of reports
    reports = {}

    htmlFile = generate_html_report(reportData)
    
    reports["viewable"] = htmlFile
    reports["allFormats"] = [htmlFile]

    logger.info("Exiting create_report_artifacts")
    
    return reports 


#------------------------------------------------------------------#
def generate_html_report(reportData):
    logger.info("    Entering generate_html_report")

    reportName = reportData["reportName"]
    projectNames  = reportData["projectNames"]
    inventoryData = reportData["inventoryData"]
    primaryProjectName = projectNames[0]
    
    scriptDirectory = os.path.dirname(os.path.realpath(__file__))
    cssFile =  os.path.join(scriptDirectory, "html-assets/css/revenera_common.css")
    logoImageFile =  os.path.join(scriptDirectory, "html-assets/images/logo_reversed.svg")
    iconFile =  os.path.join(scriptDirectory, "html-assets/images/favicon-revenera.ico")
    logger.debug("cssFile: %s" %cssFile)
    logger.debug("imageFile: %s" %logoImageFile)
    logger.debug("iconFile: %s" %iconFile)


    #########################################################
    #  Encode the image files
    encodedLogoImage = encodeImage(logoImageFile)
    encodedfaviconImage = encodeImage(iconFile)

    # Grab the current date/time for report date stamp
    now = datetime.now().strftime("%B %d, %Y at %H:%M:%S")

    htmlFile = primaryProjectName.replace(" - ", "-").replace(" ", "_") + "-" + reportName.replace(" ", "_") + ".html"

    logger.debug("htmlFile: %s" %htmlFile)

    #---------------------------------------------------------------------------------------------------
    # Create a simple HTML file to display
    #---------------------------------------------------------------------------------------------------
    try:
        html_ptr = open(htmlFile,"w")
    except:
        logger.error("Failed to open htmlfile %s:" %htmlFile)
        raise

    html_ptr.write("<html>\n") 
    html_ptr.write("    <head>\n")

    html_ptr.write("        <!-- Required meta tags --> \n")
    html_ptr.write("        <meta charset='utf-8'>  \n")
    html_ptr.write("        <meta name='viewport' content='width=device-width, initial-scale=1, shrink-to-fit=no'> \n")

    html_ptr.write(''' 
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.1/css/bootstrap.min.css" integrity="sha384-VCmXjywReHh4PwowAiWNagnWcLhlEJLA5buUprzK8rxFgeH0kww/aWY76TfkUoSX" crossorigin="anonymous">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.1.3/css/bootstrap.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/1.10.21/css/dataTables.bootstrap4.min.css">
    ''')


    html_ptr.write("        <style>\n")

    # Add the contents of the css file to the head block
    try:
        f_ptr = open(cssFile)
        logger.debug("Adding css file details")
        for line in f_ptr:
            html_ptr.write("            %s" %line)
        f_ptr.close()
    except:
        logger.error("Unable to open %s" %cssFile)
        print("Unable to open %s" %cssFile)

    # TODO Add to css file
    html_ptr.write(" .tr-notExactMatch { background-color: #F0F0F0;}\n")
    html_ptr.write(" .td-nomatch { color: #F80000;}\n")
    # To keep the filter button a different color after it was clicked
    html_ptr.write(".active {  background-color: #89EE46; color: #000000; outline-color: red;}")

    
    html_ptr.write("        </style>\n")  

    html_ptr.write("    	<link rel='icon' type='image/png' href='data:image/png;base64, {}'>\n".format(encodedfaviconImage.decode('utf-8')))
    html_ptr.write("        <title>%s</title>\n" %(reportName.upper()))
    html_ptr.write("    </head>\n") 

    html_ptr.write("<body>\n")
    html_ptr.write("<div class=\"container-fluid\">\n")

    #---------------------------------------------------------------------------------------------------
    # Report Header
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN HEADER -->\n")
    html_ptr.write("<div class='header'>\n")
    html_ptr.write("  <div class='logo'>\n")
    html_ptr.write("    <img src='data:image/svg+xml;base64,{}' style='width: 400px;'>\n".format(encodedLogoImage.decode('utf-8')))
    html_ptr.write("  </div>\n")
    html_ptr.write("<div class='report-title'>%s</div>\n" %reportName)
    html_ptr.write("</div>\n")
    html_ptr.write("<!-- END HEADER -->\n")


    #---------------------------------------------------------------------------------------------------
    # Body of Report
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN BODY -->\n")  


    html_ptr.write('''<div class="btn-toolbar" role="toolbar" aria-label="button toolbar">\n''')
    html_ptr.write('''    <div class="btn-group mr-2" role="group" aria-label="common" >''')
    html_ptr.write('''        <button  type="button" class="btn  btn-revenera-gray" id="hideNonExact">Show Common Components</button>\n''')
    html_ptr.write('''    </div>\n''')
    html_ptr.write('''    <div class="btn-group mr-2" role="group" aria-label="diffs">''')
    html_ptr.write('''        <button id="hideExact" type="button" class="btn btn-revenera-gray">Show Differences</button>\n''')
    html_ptr.write('''    </div>\n''')
    html_ptr.write('''    <div class="btn-group" role="group" aria-label="all">''')
    html_ptr.write('''         <button id="reset" type="button" class="btn btn-revenera-gray">Show All</button>\n''')
    html_ptr.write('''    </div>\n''')
    html_ptr.write('''</div>\n''')


    html_ptr.write('''<p>''')
    html_ptr.write('''<p>''')

    html_ptr.write("<table id='comparisonData' class='table table-hover row-border table-sm' style='width:90%'>\n")

    html_ptr.write("<colgroup>\n")
    html_ptr.write("<col span=\"1\" style=\"width: 30%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 20%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 10%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 20%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 10%;\">\n")
    html_ptr.write("</colgroup>\n")


    html_ptr.write("    <thead>\n")
    html_ptr.write("        <tr>\n")
    html_ptr.write("            <th colspan='1' class='text-center'>&nbsp</th>\n")  
    html_ptr.write("            <th colspan='2' class='text-center'><h4>%s</h4></th>\n" %projectNames[0])  
    html_ptr.write("            <th colspan='2' class='text-center'><h4>%s</h4></th>\n" %projectNames[1]) 
    html_ptr.write("        </tr>\n") 
    html_ptr.write("        <tr>\n") 
    html_ptr.write("            <th class='text-center'>COMPONENT</th>\n") 

    html_ptr.write("            <th class='text-center'>SELECTED LICENSE</th>\n") 
    html_ptr.write("            <th class='text-center'>FORGE</th>\n")

    html_ptr.write("            <th class='text-center'>SELECTED LICENSE</th>\n") 
    html_ptr.write("            <th class='text-center'>FORGE</th>\n")  
    html_ptr.write("        </tr>\n")
    html_ptr.write("    </thead>\n")  
    html_ptr.write("    <tbody>\n")  


    ######################################################
    # Cycle through the inventory to create the 
    # table with the results
    for component in sorted(inventoryData):

        # Is the component part of the first project?
        if projectNames[0] in inventoryData[component].keys():
            proj1_selectedLicenseName = inventoryData[component][projectNames[0]]['selectedLicenseName'] 
            proj1_componentForgeName = inventoryData[component][projectNames[0]]['componentForgeName']
        else:
            proj1_selectedLicenseName = ""
            proj1_componentForgeName = ""

        # Is the component part of the second project?
        if projectNames[1] in inventoryData[component].keys():
            proj2_selectedLicenseName = inventoryData[component][projectNames[1]]['selectedLicenseName'] 
            proj2_componentForgeName = inventoryData[component][projectNames[1]]['componentForgeName']
        else:
            proj2_selectedLicenseName = ""
            proj2_componentForgeName = ""

        ################################################
        # Is this an exact match between projects?
        if proj1_selectedLicenseName == proj2_selectedLicenseName and proj1_selectedLicenseName == proj2_selectedLicenseName and proj1_componentForgeName == proj2_componentForgeName:
            matchType = "CVL"
            html_ptr.write("        <tr matchType='%s'> \n" %matchType)
        else:
            matchType = "CV"
            html_ptr.write("        <tr class='tr-notExactMatch' matchType='%s'> \n" %matchType)
        
        html_ptr.write("            <td class='text-left'>%s</th>\n" %(component))
        
        if proj1_selectedLicenseName != proj2_selectedLicenseName and proj1_selectedLicenseName != "" and proj2_selectedLicenseName != "": 
            html_ptr.write("            <td class='td-nomatch text-left'>%s</th>\n" %proj1_selectedLicenseName)
        else:
            html_ptr.write("            <td class='text-left'>%s</th>\n" %proj1_selectedLicenseName)
        
        if proj1_componentForgeName != proj2_componentForgeName and proj1_componentForgeName != "" and proj2_componentForgeName != "": 
            html_ptr.write("            <td class='td-nomatch text-left'>%s</th>\n" %proj1_componentForgeName)
        else:
            html_ptr.write("            <td class='text-left'>%s</th>\n" %proj1_componentForgeName)

        
        if proj1_selectedLicenseName != proj2_selectedLicenseName and proj1_selectedLicenseName != "" and proj2_selectedLicenseName != "": 
            html_ptr.write("            <td class='td-nomatch text-left'>%s</th>\n" %proj2_selectedLicenseName)
        else:
            html_ptr.write("            <td class='text-left'>%s</th>\n" %proj2_selectedLicenseName)

        if proj1_componentForgeName != proj2_componentForgeName and proj1_componentForgeName != "" and proj2_componentForgeName != "": 
            html_ptr.write("            <td class='td-nomatch text-left'>%s</th>\n" %proj2_componentForgeName)
        else:
            html_ptr.write("            <td class='text-left'>%s</th>\n" %proj2_componentForgeName)

        html_ptr.write("        </tr>\n") 
    html_ptr.write("    </tbody>\n")

    html_ptr.write("</table>\n")  

    html_ptr.write("<!-- END BODY -->\n")  

    #---------------------------------------------------------------------------------------------------
    # Report Footer
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN FOOTER -->\n")
    html_ptr.write("<div class='report-footer'>\n")
    html_ptr.write("  <div style='float:left'>&copy; 2020 Revenera</div>\n")
    html_ptr.write("  <div style='float:right'>Generated on %s</div>\n" %now)
    html_ptr.write("</div>\n")
    html_ptr.write("<!-- END FOOTER -->\n")  

    html_ptr.write("</div>\n")

    #---------------------------------------------------------------------------------------------------
    # Add javascript 
    #---------------------------------------------------------------------------------------------------

    html_ptr.write('''

    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>  
    <script src="https://cdn.datatables.net/1.10.21/js/dataTables.bootstrap4.min.js"></script> 

    ''')


    html_ptr.write('''
        <script>
            var table = $('#comparisonData').DataTable();

            $("#hideExact").click(function() {
                $.fn.dataTable.ext.search.pop();
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return $(table.row(dataIndex).node()).attr('matchType') == "CV";
                }
            );
            table.draw();
            }); 


            $("#hideNonExact").click(function() {
            $.fn.dataTable.ext.search.pop();
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {

                    return $(table.row(dataIndex).node()).attr('matchType') == "CVL";
                    }
                );
                table.draw();
            });    
            $("#reset").click(function() {
                $.fn.dataTable.ext.search.pop();
                table.draw();
            });


            $(document).ready(function () {
                $('button').on('click', function() {
                $('button').removeClass('active');
                $(this).addClass('active');
            });
            });


            </script>


        ''')


    html_ptr.write("</body>\n") 
    html_ptr.write("</html>\n") 
    html_ptr.close() 

    logger.info("    Exiting generate_html_report")
    return htmlFile


####################################################################
def encodeImage(imageFile):

    #############################################
    # Create base64 variable for branding image
    try:
        with open(imageFile,"rb") as image:
            logger.debug("Encoding image: %s" %imageFile)
            encodedImage = base64.b64encode(image.read())
            return encodedImage
    except:
        logger.error("Unable to open %s" %imageFile)
        raise