'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Wed Dec 08 2021
File : report_artifacts_html.py
'''
import logging, os, base64
import _version

logger = logging.getLogger(__name__)

#------------------------------------------------------------------#
def generate_html_report(reportData):
    logger.info("    Entering generate_html_report")

    reportName = reportData["reportName"]   
    reportFileNameBase = reportData["reportFileNameBase"]
    reportTimeStamp =  reportData["reportTimeStamp"] 
    primaryProjectName = reportData["primaryProjectName"]
    primaryProjectInventoryCount = reportData["primaryProjectInventoryCount"]
    otherProjectName = reportData["otherProjectName"]
    otherProjectInventoryCount = reportData["otherProjectInventoryCount"]
    largestHierachy = reportData["largestHierachy"]
    reportOptions = reportData["reportOptions"]
    includeUnpublishedInventory = reportOptions["includeUnpublishedInventory"]  # True/False
    tableData = reportData["tableData"]
    
    scriptDirectory = os.path.dirname(os.path.realpath(__file__))
    cssFile =  os.path.join(scriptDirectory, "common/branding/css/revenera_common.css")
    logoImageFile =  os.path.join(scriptDirectory, "common/branding/images/logo_reversed.svg")
    iconFile =  os.path.join(scriptDirectory, "common/branding/images/favicon-revenera.ico")

    #########################################################
    #  Encode the image files
    encodedLogoImage = encodeImage(logoImageFile)
    encodedfaviconImage = encodeImage(iconFile)

    htmlFile = reportFileNameBase + ".html"

    logger.debug("        htmlFile: %s" %htmlFile)

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
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" integrity="sha384-xOolHFLEh07PJGoPkLv1IbcEPTNtaed2xpHsD9ESMhqIYd0nLMwNLD69Npy4HI+N" crossorigin="anonymous">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.6.2/css/bootstrap.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/dataTables.bootstrap4.min.css">
        <link rel="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.16/themes/default/style.min.css">              
    ''')


    html_ptr.write("        <style>\n")

    # Add the contents of the css file to the head block
    try:
        f_ptr = open(cssFile)
        logger.debug("        Adding css file details")
        for line in f_ptr:
            html_ptr.write("            %s" %line)
        f_ptr.close()
    except:
        logger.error("Unable to open %s" %cssFile)
        print("Unable to open %s" %cssFile)

    # TODO Add to css file
    html_ptr.write(" .tr-notExactMatch { background-color: #F0F0F0;}\n")
    html_ptr.write(" .td-nomatch { color: #F80000;}\n")
    html_ptr.write(" .btn-comparison {  width:250px; background-color: #323E48; color: #FFFFFF;}\n")
    # To keep the filter button a different color after it was clicked
    html_ptr.write(".active {  background-color: #89EE46; color: #000000; outline-color: red;}")

    
    html_ptr.write("        </style>\n")  

    html_ptr.write("    	<link rel='icon' type='image/png' href='data:image/png;base64, {}'>\n".format(encodedfaviconImage.decode('utf-8')))
    html_ptr.write("        <title>%s</title>\n" %(reportName))
    html_ptr.write("    </head>\n") 

    html_ptr.write("<body>\n")
    html_ptr.write("<div class=\"container-fluid\">\n")

    #---------------------------------------------------------------------------------------------------
    # Report Header
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN HEADER -->\n")
    html_ptr.write("<div class='header'>\n")
    html_ptr.write("  <div class='logo'>\n")
    html_ptr.write("    <img src='data:image/svg+xml;base64,{}' style='height: 5%'>\n".format(encodedLogoImage.decode('utf-8')))
    html_ptr.write("  </div>\n")
    html_ptr.write("<div class='report-title'>%s</div>\n" %reportName)
    html_ptr.write("</div>\n")
    html_ptr.write("<!-- END HEADER -->\n")


    #---------------------------------------------------------------------------------------------------
    # Body of Report
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN BODY -->\n")  

    # Is there at least one hierarchy that is being displayed?
    if largestHierachy > 1:
        
        html_ptr.write("<hr class='small'>\n")

        #######################################################################
        #  Create table to hold the project summary charts.
        #  js script itself is added later

        html_ptr.write("<div class='container'>\n")
        html_ptr.write("    <div class='row'>\n")

        html_ptr.write("        <div class='col-sm'>\n")
        html_ptr.write("<h6 class='gray' style='padding-top: 10px;'><center>%s<br>Project Hierarchy<br>(%s Total Items)</center></h6>" %(otherProjectName, otherProjectInventoryCount["total"]) )
        html_ptr.write("            <div id='project_hierarchy1'></div>\n")
        html_ptr.write("        </div>\n")

        html_ptr.write("        <div class='col-sm'>\n")
        html_ptr.write("<h6 class='gray' style='padding-top: 10px;'><center>%s<br>Project Hierarchy<br>(%s Total Items)</center></h6>" %(primaryProjectName, primaryProjectInventoryCount["total"]) )
        html_ptr.write("            <div id='project_hierarchy2'></div>\n")
        html_ptr.write("        </div>\n")

        html_ptr.write("    </div>\n")
        html_ptr.write("</div>\n")

        html_ptr.write("<hr class='small'>")

    html_ptr.write('''<div style="text-align: center;">''')
    html_ptr.write('''  <div class="btn-group" role="group" aria-label="data filters"">\n''')   
    html_ptr.write('''      <button id="showAll" type="button" class="btn-comparison mx-1 my-2">Show All Items</button>\n''')
    html_ptr.write('''      <button id="showUnchanged" type="button" class="btn btn-comparison mx-2 my-2">Show Unchanged Items</button>\n''')

    html_ptr.write('''      <div class="btn-group " role="group">\n''')
    
    html_ptr.write('''          <button id="showDifferences" type="button" class="btn btn-comparison mx-1 my-2 dropdown-toggle" data-toggle="dropdown" aria-expanded="false">Show Differences</button>\n''')
    html_ptr.write('''          <div class="dropdown-menu" role="group" aria-labelledby="dropdownMenu">\n''')
    html_ptr.write('''              <button id="showAllDifferences" class="dropdown-item" type="button" onclick="showDifference(this)">All Differences</button>\n''')
    html_ptr.write('''              <button id="showVersionDifferences" class="dropdown-item" type="button" onclick="showDifference(this)">Versions Differences</button>\n''')
    html_ptr.write('''              <button id="showLicenseDifferences" class="dropdown-item" type="button" onclick="showDifference(this)">Licenses Differences</button>\n''')
    if includeUnpublishedInventory:
        html_ptr.write('''          <button id="showPublishedDifferences" class="dropdown-item" type="button" onclick="showDifference(this)">Published State</button>\n''')
    html_ptr.write('''              <button id="showUnreconcilable" class="dropdown-item" type="button" onclick="showDifference(this)">Unreconcilable Items</button>\n''')
    html_ptr.write('''          </div>\n''')
    html_ptr.write('''      </div>\n''')
    
    html_ptr.write('''  </div>\n''')

    html_ptr.write('''  <button id="showRemoved" type="button" class="btn btn-comparison mx-1 my-2">Show Removed Items</button>\n''')
    html_ptr.write('''  <button id="showAdded" type="button" class="btn btn-comparison mx-1 my-2">Show Added Items</button>\n''')
    

    html_ptr.write('''</div>\n''')

    html_ptr.write('''<p>\n''')
    html_ptr.write('''<p>\n''')

    html_ptr.write("<table id='comparisonData' class='table table-hover row-border table-sm' style='width:90%'>\n")

    html_ptr.write("<colgroup>\n")
    html_ptr.write("<col span=\"1\" style=\"width: 20%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 15%;\">\n")
    if includeUnpublishedInventory:
        html_ptr.write("<col span=\"1\" style=\"width: 5%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 10%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 10%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 15%;\">\n")
    if includeUnpublishedInventory:
        html_ptr.write("<col span=\"1\" style=\"width: 5%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 10%;\">\n")
    html_ptr.write("<col span=\"1\" style=\"width: 10%;\">\n")
    html_ptr.write("</colgroup>\n")

    html_ptr.write("    <thead>\n")
    html_ptr.write("        <tr>\n")
    html_ptr.write("            <th colspan='1' class='text-center'>&nbsp</th>\n") 

    if includeUnpublishedInventory:
        headerColSpan = 4
    else:
        headerColSpan = 3

    html_ptr.write("            <th colspan='%s' class='text-center'><h4>%s</h4></th>\n" %(headerColSpan, otherProjectName))
    html_ptr.write("            <th colspan='%s' class='text-center'><h4>%s</h4></th>\n" %(headerColSpan, primaryProjectName))
    html_ptr.write("        </tr>\n") 
    html_ptr.write("        <tr>\n") 
    html_ptr.write("            <th class='text-center'>COMPONENT</th>\n") 
    html_ptr.write("            <th class='text-center'>VERSION</th>\n")
    html_ptr.write("            <th class='text-center'>LICENSE</th>\n")
    html_ptr.write("            <th class='text-center'>PROJECTS</th>\n")
    if includeUnpublishedInventory:
        html_ptr.write("            <th class='text-center'>PUBLISHED STATE</th>\n")
    html_ptr.write("            <th class='text-center'>VERSION</th>\n")
    html_ptr.write("            <th class='text-center'>LICENSE</th>\n")
    html_ptr.write("            <th class='text-center'>PROJECTS</th>\n")
    if includeUnpublishedInventory:
        html_ptr.write("            <th class='text-center'>PUBLISHED STATE</th>\n")

    html_ptr.write("        </tr>\n")
    html_ptr.write("    </thead>\n")  

    html_ptr.write("    <tbody>\n")  

    for row in tableData:
        component = row[0]

        otherProjectVersion =  "&nbsp" if row[1] is None else row[1] 
        otherProjectLicense = "&nbsp" if row[2] is None else row[2] 
        otherProjectProjects = ["&nbsp"] if row[3] is None else row[3] 
        otherProjectPublicationState = "&nbsp" if row[4] is None else row[4]

        primaryProjectVersion =    "&nbsp" if row[5] is None else row[5] 
        primaryProjectLicense =    "&nbsp" if row[6] is None else row[6] 
        primaryProjectProjects =   ["&nbsp"] if row[7] is None else row[7] 
        primaryProjectPublicationState =  "&nbsp" if row[8] is None else row[8]
        matchType = row[9] 

        html_ptr.write("        <tr matchType='%s'> \n" %matchType)
        html_ptr.write("            <td class='text-left'>%s</th>\n" %(component))

        

        tdclass = 'text-left' if "V" in matchType or "added" in matchType  or "removed" in matchType or "unreconcilable" in matchType else "td-nomatch text-left"
        html_ptr.write("            <td class='%s'>%s</th>\n" %(tdclass, otherProjectVersion))
        tdclass = 'text-left' if "L" in matchType or "added" in matchType  or "removed" in matchType or "unreconcilable" in matchType else "td-nomatch text-left"
        html_ptr.write("            <td class='%s'>%s</th>\n" %(tdclass, otherProjectLicense))
        
        # Provide hyperlinks to inventory item for each item within the projct        
        if otherProjectProjects == ["&nbsp"]:
            html_ptr.write("            <td class='text-left'>&nbsp</th>\n")
        else:
            html_ptr.write("            <td class='text-left'>")
            
            projectNames = otherProjectProjects.keys()
            for projectName in projectNames:
                inventoryLinks = otherProjectProjects[projectName]
                for inventoryLink in inventoryLinks:                    
                    html_ptr.write("<a href='%s' target='_blank' >%s</a><br>" %(inventoryLink, projectName))
                     
            html_ptr.write("</th>\n")

        if includeUnpublishedInventory:
            tdclass = 'text-left' if "P" in matchType or "added" in matchType  or "removed" in matchType or "unreconcilable" in matchType else "td-nomatch text-left"
            html_ptr.write("            <td class='%s'>%s</th>\n" %(tdclass, otherProjectPublicationState))

        tdclass = 'text-left' if "V" in matchType or "added" in matchType  or "removed" in matchType or "unreconcilable" in matchType else "td-nomatch text-left"
        html_ptr.write("            <td class='%s'>%s</th>\n" %(tdclass, primaryProjectVersion))
        
        tdclass = 'text-left' if "L" in matchType or "added" in matchType  or "removed" in matchType or "unreconcilable" in matchType else "td-nomatch text-left"
        html_ptr.write("            <td class='%s'>%s</th>\n" %(tdclass, primaryProjectLicense))

        # Provide hyperlinks to inventory item for each item within the projct        
        if primaryProjectProjects == ["&nbsp"]:
            html_ptr.write("            <td class='text-left'>&nbsp</th>\n")
        else:
            html_ptr.write("            <td class='text-left'\n>")
            
            projectNames = primaryProjectProjects.keys()
            for projectName in projectNames:
                inventoryLinks = primaryProjectProjects[projectName]
                for inventoryLink in inventoryLinks:                    
                    html_ptr.write("<a href='%s' target='_blank' >%s</a><br>\n" %(inventoryLink, projectName))
                     
            html_ptr.write("</th>\n")
              
        if includeUnpublishedInventory:
            tdclass = 'text-left' if "P" in matchType or "added" in matchType  or "removed" in matchType or "unreconcilable" in matchType else "td-nomatch text-left"
            html_ptr.write("            <td class='%s'>%s</th>\n" %(tdclass, primaryProjectPublicationState))



        html_ptr.write("        </tr>\n") 

    html_ptr.write("    </tbody>\n")

    html_ptr.write("</table>\n")  

    html_ptr.write("<!-- END BODY -->\n")  

    #---------------------------------------------------------------------------------------------------
    # Report Footer
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN FOOTER -->\n")
    html_ptr.write("<div class='report-footer'>\n")
    html_ptr.write("  <div style='float:right'>Generated on %s</div>\n" %reportTimeStamp)
    html_ptr.write("<br>\n")
    html_ptr.write("  <div style='float:right'>Report Version: %s</div>\n" %_version.__version__)
    html_ptr.write("</div>\n")
    html_ptr.write("<!-- END FOOTER -->\n")  

    html_ptr.write("</div>\n")

    #---------------------------------------------------------------------------------------------------
    # Add javascript 
    #---------------------------------------------------------------------------------------------------

    html_ptr.write('''

    <script src="https://code.jquery.com/jquery-3.7.1.slim.min.js" integrity="sha256-kmHvs0B+OpCW5GVHUNjv9rOmY0IvSIRcf7zGUDTDQM8=" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js" integrity="sha384-9/reFTGAW83EW2RDu2S0VKaIzap3H66lZH81PoYlFhbGU+6BZp6G7niu735Sk7lN" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.min.js" integrity="sha384-+sLIOodYLS7CIrQpBjl+C7nPvqq+FbNUBDunl/OZv93DB7Ln/533i8e/mZXLi/P+" crossorigin="anonymous"></script>   
    <script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>  
    <script src="https://cdn.datatables.net/1.13.8/js/dataTables.bootstrap4.min.js"></script> 
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.16/jstree.min.js"></script>

    ''')


    html_ptr.write("<script>\n")

    if largestHierachy > 1:
        # Add the js for the project summary stacked bar charts
        generate_project_hierarchy_tree(html_ptr, reportData["otherProjectList"], otherProjectInventoryCount, primaryProjectInventoryCount, "project_hierarchy1")
        generate_project_hierarchy_tree(html_ptr, reportData["primaryProjectList"], primaryProjectInventoryCount, otherProjectInventoryCount, "project_hierarchy2")
        
    
    html_ptr.write('''
            var table = $('#comparisonData').DataTable(
                {"lengthMenu": [ [25, 50, 100, -1], [25, 50, 100, "All"] ],}
            );

            // Used to change the button text to the value of the selected filter 
            // from within the dropdown list      
            function showDifference(item) {
                document.getElementById('showDifferences').innerHTML = item.innerHTML;
            }


            $("#showAll").click(function() {
                $.fn.dataTable.ext.search.pop();
                document.getElementById('showDifferences').innerHTML = "Show Differences";
                table.draw();
            });


            $("#showUnchanged").click(function() {
                $.fn.dataTable.ext.search.pop();
                document.getElementById('showDifferences').innerHTML = "Show Differences";
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return $(table.row(dataIndex).node()).attr('matchType') == "CVLP";
                }
            );
            table.draw();
            }); 

                   
            $("#showAllDifferences").click(function() {
                $.fn.dataTable.ext.search.pop();
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return $(table.row(dataIndex).node()).attr('matchType') != "CVLP";
                }
            );
            table.draw();
            });                    


            $("#showVersionDifferences").click(function() {
                $.fn.dataTable.ext.search.pop();
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return !($(table.row(dataIndex).node()).attr('matchType').includes("V") ||
                             $(table.row(dataIndex).node()).attr('matchType') == "addedToPrimaryProject" ||
                                $(table.row(dataIndex).node()).attr('matchType') == "removedFromOtherProject" ||
                                $(table.row(dataIndex).node()).attr('matchType') == "unreconcilable"
                    );
                }
            );
            table.draw();
            }); 
                   
            $("#showLicenseDifferences").click(function() {
                $.fn.dataTable.ext.search.pop();
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return !($(table.row(dataIndex).node()).attr('matchType').includes("L") ||
                             $(table.row(dataIndex).node()).attr('matchType') == "addedToPrimaryProject" ||
                                $(table.row(dataIndex).node()).attr('matchType') == "removedFromOtherProject" ||
                                $(table.row(dataIndex).node()).attr('matchType') == "unreconcilable"
                    );
                }
            );
            table.draw();
            }); 

            $("#showPublishedDifferences").click(function() {
                $.fn.dataTable.ext.search.pop();
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return !($(table.row(dataIndex).node()).attr('matchType').includes("P") ||
                             $(table.row(dataIndex).node()).attr('matchType') == "addedToPrimaryProject" ||
                                $(table.row(dataIndex).node()).attr('matchType') == "removedFromOtherProject" ||
                                $(table.row(dataIndex).node()).attr('matchType') == "unreconcilable"
                    );
                }
            );
            table.draw();
            }); 

            $("#showUnreconcilable").click(function() {
                $.fn.dataTable.ext.search.pop();
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return $(table.row(dataIndex).node()).attr('matchType') == "unreconcilable";                }
            );
            table.draw();
            }); 
               
            $("#showAdded").click(function() {
                $.fn.dataTable.ext.search.pop();
                document.getElementById('showDifferences').innerHTML = "Show Differences";
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return $(table.row(dataIndex).node()).attr('matchType') == "addedToPrimaryProject";
                }
            );
            table.draw();
            }); 
                
            $("#showRemoved").click(function() {
                $.fn.dataTable.ext.search.pop();
                document.getElementById('showDifferences').innerHTML = "Show Differences";
                $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return $(table.row(dataIndex).node()).attr('matchType') == "removedFromOtherProject";
                }
            );
            table.draw();
            }); 


            $(document).ready(function () {
                $('button').on('click', function() {
                $('button').removeClass('active');
                $(this).addClass('active');
            });
            });

        ''')

    html_ptr.write("</script>\n")


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
            encodedImage = base64.b64encode(image.read())
            return encodedImage
    except:
        logger.error("Unable to open %s" %imageFile)
        raise

#----------------------------------------------------------------------------------------#
def generate_project_hierarchy_tree(html_ptr, projectHierarchy, thisProjectInventoryCount, otherProjectInventoryCount, chartIdentifier):
    logger.info("Entering generate_project_hierarchy_tree")

    projectIDList = list((otherProjectInventoryCount.keys()))  # Get the project IDs for the comparison project

    html_ptr.write('''var hierarchy = [\n''')

    for project in projectHierarchy:

        projectID = project["projectID"]

        # is this the top most parent or a child project with a parent
        if "uniqueID" in project:
            projectIdentifier = project["uniqueID"]
        else:
            projectIdentifier = projectID

        inventoryCount = thisProjectInventoryCount[projectID]

        if projectID in projectIDList:
            linkColor = "lime"
        else:
            linkColor = "black"

        html_ptr.write('''{
            'id': '%s', 
            'parent': '%s', 
            'text': '%s (%s items)',
            'a_attr': {
                'href': '%s'
            },
			'li_attr' : {
				'style' : 'color: %s;'
			}
        },\n'''  %(projectIdentifier, project["parent"], project["projectName"], inventoryCount, project["projectLink"], linkColor))

    html_ptr.write('''\n]''')

    html_ptr.write('''

        $('#''' + chartIdentifier + '''').jstree({ 'core' : {
            'data' : hierarchy
        } });
    ''')

    html_ptr.write('''
        $('#''' + chartIdentifier + '''').on('ready.jstree', function() {
            $("#''' + chartIdentifier + '''").jstree("open_all");               

        $("#''' + chartIdentifier + '''").on("click", ".jstree-anchor", function(evt)
        {
            var link = $(evt.target).attr("href");
            window.open(link, '_blank');
        });


        });

    ''' )