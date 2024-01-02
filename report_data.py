'''
Copyright 2020 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Aug 07 2020
File : report_data.py
'''

import logging
import common.api.project.get_project_inventory
import common.api.project.get_inventory_summary
import common.project_heirarchy
import common.api.license.license_lookup

logger = logging.getLogger(__name__)

licenseMappings = {}

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, authToken, reportData):
    logger.info("Entering gather_data_for_report")

    primaryProjectID = reportData["primaryProjectID"]
    otherProjectID = reportData["otherProjectID"]
    largestHierachy = 0

    tableData = []

    # Get inventory details for primary project
    primaryProjectList, primaryProjectInventoryData = get_project_details(baseURL, authToken, primaryProjectID, reportData)

    if "errorMsg" in primaryProjectInventoryData:
        print(primaryProjectInventoryData)

    primaryProjectName = primaryProjectList[0]["projectName"]

    # How much space will be required for the hierarchies display?
    if len(primaryProjectList) > largestHierachy:
        largestHierachy = len(primaryProjectList)
       
    # Get inventory details for primary project
    otherProjectList, otherProjectInventoryData = get_project_details(baseURL, authToken, otherProjectID, reportData)
    otherProjectName = otherProjectList[0]["projectName"]

    
    # How much space will be required for the hierarchies display?
    if len(otherProjectList) > largestHierachy:
        largestHierachy = len(otherProjectList)

    setPrimaryProjectInventoryData = set(primaryProjectInventoryData)
    setOtherProjectInventoryData = set(otherProjectInventoryData)

    commonComponents = list((setPrimaryProjectInventoryData).intersection(setOtherProjectInventoryData))
    addedToPrimaryProject_C = list((setPrimaryProjectInventoryData).difference(setOtherProjectInventoryData))
    removedFromOtherProject_C = list((setOtherProjectInventoryData).difference(setPrimaryProjectInventoryData))

    # Get data for the components that are in common to both reports
    for componentId in commonComponents:
        componentName = primaryProjectInventoryData[componentId]["componentName"]
        tableRows = compare_CV(componentName, primaryProjectInventoryData[componentId], otherProjectInventoryData[componentId])

        for tableRow in tableRows:
            # Based on the results determine the matchType      
            otherProjectVersion =   tableRow[1] 
            otherProjectLicense =  tableRow[2] 
            otherProjectPublicationState =  tableRow[4] 
            primaryProjectVersion =    tableRow[5] 
            primaryProjectLicense =    tableRow[6] 
            primaryProjectPublicationState =   tableRow[8] 

            matchType = "C" # At a bare minimum the components match here

            if primaryProjectVersion == otherProjectVersion:
                matchType += "V"
            if primaryProjectLicense == otherProjectLicense:
                matchType += "L"
            if primaryProjectPublicationState == otherProjectPublicationState:
                matchType += "P"

            tableRow.append(matchType)
            tableData.append(tableRow)
    
    # Get data for the components that are unique to the primary project
    for component in addedToPrimaryProject_C:
        matchType = "addedToPrimaryProject"
        componentName = primaryProjectInventoryData[component]["componentName"]
        partialRows = process_unique_component(primaryProjectInventoryData[component]["componentVersions"])

        if "errorMsg" in partialRows:
            return {"errorMsg", "%s for %s - %s" %(partialRows["errorMsg"], component, componentName)}
        
        for partialRow in partialRows:
            tableRow = [componentName, None, None, None, None] + partialRow + [matchType]
            tableData.append(tableRow)

    # Get data for the components that are unique to the other project
    for component in removedFromOtherProject_C:
        matchType = "removedFromOtherProject"
        componentName = otherProjectInventoryData[component]["componentName"]
        partialRows = process_unique_component(otherProjectInventoryData[component]["componentVersions"])

        if "errorMsg" in partialRows:
            return {"errorMsg", "%s for %s - %s" %(partialRows["errorMsg"], component, componentName)}

        for partialRow in partialRows:
            tableRow = [componentName] + partialRow + [None, None, None, None, matchType]
            tableData.append(tableRow)

    # Sort the information by the component name
    tableData = sorted(tableData, key=lambda x: x[0])

    reportData["primaryProjectName"] = primaryProjectName
    reportData["primaryProjectList"] = primaryProjectList
    reportData["otherProjectName"] = otherProjectName
    reportData["otherProjectList"] = otherProjectList
    reportData["largestHierachy"] = largestHierachy
    reportData["tableData"] = tableData
  
    return reportData

#------------------------------------------
def get_project_details(baseURL, authToken, projectID, reportData):
    inventoryData = {} # Create a dictionary containing the inventory data using name strings as keys

    reportOptions = reportData["reportOptions"]
    releaseVersion = reportData["releaseVersion"]
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False
    includeUnpublishedInventory = reportOptions["includeUnpublishedInventory"]  # True/False

    projectList = common.project_heirarchy.create_project_heirarchy(baseURL, authToken, projectID, includeChildProjects)

    #  Gather the details for each project and summerize the datas
    for project in projectList:

        projectID = project["projectID"]
        projectName = project["projectName"]

        if includeUnpublishedInventory:
            publishedStates = ["PUBLISHED", "UNPUBLISHED"]
        else:
            publishedStates = ["PUBLISHED"] 

        for publishedState in publishedStates:

            logger.info("        Getting %s inventory for project: %s" %(publishedState.lower(), projectName))
            print("        Getting %s inventory for project: %s" %(publishedState.lower(), projectName))

            APIOPTIONS = "&includeFiles=false&skipVulnerabilities=true&published=%s" %publishedState       
            projectInventoryResponse = common.api.project.get_inventory_summary.get_project_inventory_summary(baseURL, projectID, authToken, APIOPTIONS)

            if "errorMsg" in projectInventoryResponse:
                return None, projectInventoryResponse
            
            print("            %s items returned." %len(projectInventoryResponse))

            # For display purposes
            publishedState = "Published" if publishedState == "PUBLISHED" else "Not Published" 


            # Cycle through each item to get the CVL data
            for inventoryItem in projectInventoryResponse:
                inventoryId = inventoryItem["id"]
                componentId = inventoryItem["componentId"]
                componentName = inventoryItem["componentName"]
                componentVersionName = inventoryItem["componentVersionName"]
                selectedLicenseId = inventoryItem["selectedLicenseId"]
                selectedLicense = inventoryItem["selectedLicenseSPDXIdentifier"] 

                inventoryLink = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(projectID) + "&tab=projectInventory&pinv=" + str(inventoryId)
                              
                # for WIP and LO items use the inventory item name vs the componentId
                inventoryType = inventoryItem["type"]
                if inventoryType == "Work in Progress":
                    componentId = inventoryItem["name"]
                    componentName = inventoryItem["name"]
                    componentVersionName = "Work in Progress"
                elif inventoryType == "License Only":
                    componentId = inventoryItem["name"]
                    componentName = inventoryItem["name"]
                    componentVersionName = "License Only"

                # The project summary API currently returns the full license name 
                # and not the SPDX ID so create mapping    
                if releaseVersion <= "2024R3":
                    if selectedLicenseId != "N/A":

                        if selectedLicenseId in licenseMappings:
                            selectedLicense = licenseMappings[selectedLicenseId]            
                        else:
                            logger.debug("Collecting license details for license id: %s" %selectedLicenseId)
                            licenseDetails = common.api.license.license_lookup.get_license_details(baseURL, selectedLicenseId, authToken)

                            if "errorMsg" in licenseDetails:
                                logger.error("Error getting licese details for id: %s" %selectedLicenseId)
                                return None, licenseDetails

                            selectedLicense = licenseDetails["spdxIdentifier"]
                    
                            if selectedLicense == "":
                                selectedLicense = licenseDetails["shortName"]
                            
                            licenseMappings[selectedLicenseId] = selectedLicense
                    else:
                        selectedLicense = "N/A"

                # Determine if this is a new component for this project (parent/children) or another occurance
                if componentId in inventoryData:     
                    if componentVersionName in inventoryData[componentId]["componentVersions"]:
                        if selectedLicense in inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"]:
                            if publishedState in inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"]:
                                    if projectName in inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"]:
                                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName].append(inventoryLink)
                                    else:
                                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"] = {}
                                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName] = []
                                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName].append(inventoryLink)
                            else:
                                inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState] = {}
                                inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"] = {}
                                inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName] = []
                                inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName].append(inventoryLink)
                        else:
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense] = {}
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"] = {}
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState] = {}
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"] = {}
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName] = []
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName].append(inventoryLink)
                    else:
                        inventoryData[componentId]["componentVersions"][componentVersionName] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName] = []
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName].append(inventoryLink)
                else:
                    inventoryData[componentId] = {}  # A dictionary using comp version as keys
                    inventoryData[componentId]["componentName"] = componentName
                    inventoryData[componentId]["componentVersions"] = {}  # A dictionary using selected license as keys
                    inventoryData[componentId]["componentVersions"][componentVersionName] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName] = []
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState]["projects"][projectName].append(inventoryLink)

    return projectList, inventoryData


#------------------------------------------
def compare_CV(componentName, primaryProject_C_Data, otherProject_C_Data):
    print("    Compare versions for %s" %componentName)
    tableRows = []
    primaryProject_CV_Data = primaryProject_C_Data["componentVersions"]
    otherProject_CV_Data = otherProject_C_Data["componentVersions"]

    setPrimaryProject_CV_Data = set(primaryProject_CV_Data)
    setOtherProject_CV_Data = set(otherProject_CV_Data)

    common_CV = list((setPrimaryProject_CV_Data).intersection(setOtherProject_CV_Data))
    addedToPrimaryCV= list((setPrimaryProject_CV_Data).difference(setOtherProject_CV_Data))
    removedFromOtherCV = list((setOtherProject_CV_Data).difference(setPrimaryProject_CV_Data))

    if len(common_CV) == 0:          
        print("        No common versions for: %s" %(componentName))

        if len(primaryProject_CV_Data) ==  len(otherProject_CV_Data):
            # There are an equal number of items in both projects
            if len(primaryProject_CV_Data) == 1:
                # Just a simple version change what about the license
                primaryProjectVerion = list(primaryProject_CV_Data.keys())[0]
                otherProjectVerion = list(otherProject_CV_Data.keys())[0]

                tableRow = compare_CVL(componentName, primaryProject_CV_Data, primaryProjectVerion, otherProject_CV_Data, otherProjectVerion)
                tableRows.append(tableRow)
                return tableRows
            else:
                # Same number of CV items in each project but not way to know which ones could be related
                tableRows = process_unreconcilable_CV_Items(componentName, primaryProject_CV_Data, otherProject_CV_Data)
                return tableRows
        else:
            # Different number of versions for each set and none in common and no way to determine if one is an upgrade to
            # another or not so just combine the information into a single row and mark as unreconcilable
            tableRows = process_unreconcilable_CV_Items(componentName, primaryProject_CV_Data, otherProject_CV_Data)
            return tableRows

    elif len(common_CV) == 1:  # There is at least single common versions match

        if len(addedToPrimaryCV) == 0 and len(removedFromOtherCV) == 0:
            # It is a single unique match for this component
            version = common_CV[0]
            print("        Exact version match - %s" %common_CV[0])
            tableRow = compare_CVL(componentName, primaryProject_CV_Data, version, otherProject_CV_Data, version)
            tableRows.append(tableRow)
            return tableRows
        else:
            # Along with a single exact version match there are also other entries for this component
            # Manage the exact match
            version = common_CV[0]
            print("        Exact version match - %s" %common_CV[0])
            tableRow = compare_CVL(componentName, primaryProject_CV_Data, version, otherProject_CV_Data, version)
            tableRows.append(tableRow)

            # Now deal with the unique items if there are any
            if len(addedToPrimaryCV) != 0:
                matchType = "addedToPrimaryProject"

                for version in addedToPrimaryCV:
                    # Pass the dict as the func expects it
                    partialRow = process_unique_component({version: primaryProject_CV_Data[version]})
                    
                    if "errorMsg" in partialRow:
                        return {"errorMsg", "%s for %s" %(partialRow["errorMsg"], componentName)}

                    tableRow = [componentName, None, None, None, None] + partialRow[0] + [matchType]
                    tableRows.append(tableRow)

            if len(removedFromOtherCV) !=0:
                matchType = "removedFromOtherProject"

                for version in removedFromOtherCV:
                    # Pass the dict as the func expects it
                    partialRow = process_unique_component({version: otherProject_CV_Data[version]})
                    
                    if "errorMsg" in partialRow:
                        return {"errorMsg", "%s for %s" %(partialRow["errorMsg"], componentName)}

                    tableRow = [componentName] + partialRow[0] +[ None, None, None, None, matchType]
                    tableRows.append(tableRow)
                    
            return tableRows
    
    else:  # There are mulitiple common versions for this component
        print("        Multiple common comp/versions")
        return[[componentName, None, None, None, None, "TODO", "Multiple common comp/versions", None, None]]


  #------------------------------------------
def compare_CVL(componentName, primaryProject_CV_Data, primaryProjectVerion, otherProject_CV_Data, otherProjectVerion):

    primaryProject_CVL_Data = primaryProject_CV_Data[primaryProjectVerion]["licenses"]
    otherProject_CVL_Data = otherProject_CV_Data[otherProjectVerion]["licenses"]

    print("        Compare licenses for %s : %s vs %s" %(componentName, primaryProjectVerion, otherProjectVerion))

    setprimaryProject_CVL_Data = set(primaryProject_CVL_Data)
    setotherProject_CVL_Data = set(otherProject_CVL_Data)

    common_CVL = list((setprimaryProject_CVL_Data).intersection(setotherProject_CVL_Data))
    addedToPrimary_CVL = list((setprimaryProject_CVL_Data).difference(setotherProject_CVL_Data))
    removedFromOther_CVL = list((setotherProject_CVL_Data).difference(setprimaryProject_CVL_Data))  

    if len(common_CVL) == 0: 
        if len(addedToPrimary_CVL) == len(removedFromOther_CVL):
            # Equal number of unique CVL items from each hierarchy
            if len(addedToPrimary_CVL) == 1:
                
                primaryProjectLicense = addedToPrimary_CVL[0]
                otherProjectLicense = removedFromOther_CVL[0]

                tableRow = compare_CVLP(componentName, primaryProject_CVL_Data, primaryProjectVerion, primaryProjectLicense, otherProject_CVL_Data, otherProjectVerion, otherProjectLicense)

                return tableRow
            else:
                return[[componentName, None, None, None, None, "TODO", "Multiple licenses", None, None]]
     
        else:
            return[[componentName, None, None, None, None, "TODO", "Unequal quanity of license", None, None]]
            

    elif len(common_CVL) == 1:  # Exact match for CVL so need to look at projects and published states
        license = common_CVL[0]
        print("            Exact license match - %s" %license)
 
        tableRow = compare_CVLP(componentName, primaryProject_CVL_Data, primaryProjectVerion, license, otherProject_CVL_Data, otherProjectVerion, license)
        return tableRow
    else:
        print("            Mutliple common licenses for  %s-%s-%s" %(componentName, primaryProjectVerion, otherProjectVerion))
        return[[componentName, None, None, None, None, "TODO", "Muliple Common Licenses", None, None]]

#------------------------------
def compare_CVLP(componentName, primaryProject_CVL_Data, primaryProjectVerion, primaryProjectLicense, otherProject_CVL_Data, otherProjectVerion, otherProjectLicense):

    primaryProject_CVLP_Data = primaryProject_CVL_Data[primaryProjectLicense]["publishedState"]
    otherProject_CVLP_Data = otherProject_CVL_Data[otherProjectLicense]["publishedState"]
       
    print("            Compare published state for %s : %s-%s vs %s-%s" %(componentName, primaryProjectVerion, primaryProjectLicense, otherProjectVerion, otherProjectLicense))

    setprimaryProject_CVLP_Data = set(primaryProject_CVLP_Data)
    setotherProject_CVLP_Data = set(otherProject_CVLP_Data)

    common_CVLP = list((setprimaryProject_CVLP_Data).intersection(setotherProject_CVLP_Data))
    addedToPrimary_CVLP = list((setprimaryProject_CVLP_Data).difference(setotherProject_CVLP_Data))
    removedFromOther_CVLP = list((setotherProject_CVLP_Data).difference(setprimaryProject_CVLP_Data))  

    if len(common_CVLP) == 0:          
        if len(addedToPrimary_CVLP) == len(removedFromOther_CVLP):
            # Equal number of unique CVL items from each hierarchy
            if len(addedToPrimary_CVLP) == 1:
                
                primaryProjectPublishedState = addedToPrimary_CVLP[0]
                otherProjectPublishedState = removedFromOther_CVLP[0]

                primaryProjectProjects = primaryProject_CVLP_Data[primaryProjectPublishedState]["projects"]
                otherProjectProjects = otherProject_CVLP_Data[otherProjectPublishedState]["projects"]

                tableRow = [componentName, otherProjectVerion, otherProjectLicense,  otherProjectProjects, otherProjectPublishedState, primaryProjectVerion, primaryProjectLicense, primaryProjectProjects, primaryProjectPublishedState]

                return tableRow
            
            else:
                return[[componentName, None, None, None, None, "TODO", "Equal but different counts for published state", None, None]]
            
        else:
            return[[componentName, None, None, None, None, "TODO", "Differing counts for published state", None, None]]

   
    elif len(common_CVLP) == 1:  # Exact match for CVL so need to look at projects and published states
        publishedState = common_CVLP[0]
        primaryProjectProjects = primaryProject_CVLP_Data[publishedState]["projects"]
        otherProjectProjects = otherProject_CVLP_Data[publishedState]["projects"]

        tableRow = [componentName, otherProjectVerion, otherProjectLicense,  otherProjectProjects, publishedState, primaryProjectVerion, primaryProjectLicense, primaryProjectProjects, publishedState]
        return tableRow
    else:

        return[[componentName, None, None, None, None, "TODO", "Mutliple publication states", None, None]]


#------------------------------
def process_unique_component(componentVersionDetails):

    partialRows = []

    for version in componentVersionDetails:
        licenses = componentVersionDetails[version]["licenses"]
        
        numLicenses = len(licenses)

        if numLicenses == 0:
            logger.error("No license field in component data")
            return {"errorMsg": "No license field in component data"}
        else:
            # Cycle though each license to create a row entry
            for licenseName in licenses:
                # Get the publication states for each of the CVL items
                publicationStates = licenses[licenseName]["publishedState"]
                for publicationState in publicationStates:
                    projects = licenses[licenseName]["publishedState"][publicationState]["projects"]
                    partialRows.append([version, licenseName, projects, publicationState])

    return partialRows

#----------------------------------
def process_unreconcilable_CV_Items(componentName, primaryProject_CV_Data, otherProject_CV_Data):
    tableRows = []
            
    matchType = "unreconcilable"

    partialRows = process_unique_component(primaryProject_CV_Data)

    if "errorMsg" in partialRows:
        return {"errorMsg", "%s for %s" %(partialRows["errorMsg"],  componentName)}
    
    for partialRow in partialRows:
        tableRow = [componentName, None, None, None, None] + partialRow + [matchType]
        tableRows.append(tableRow)

    partialRows = process_unique_component(otherProject_CV_Data)

    if "errorMsg" in partialRows:
        return {"errorMsg", "%s for %s" %(partialRows["errorMsg"],  componentName)}
    
    for partialRow in partialRows:
        tableRow = [componentName] + partialRow + [None, None, None, None, matchType]
        tableRows.append(tableRow)

    return tableRows



#----------------------------------------------#
def create_project_hierarchy(project, parentID, projectList, baseURL):
    logger.debug("Entering create_project_hierarchy")

    # Are there more child projects for this project?
    if len(project["childProject"]):

        # Sort by project name of child projects
        for childProject in sorted(project["childProject"], key = lambda i: i['name'] ) :

            uniqueProjectID = str(parentID) + "-" + str(childProject["id"])
            nodeDetails = {}
            nodeDetails["projectID"] = childProject["id"]
            nodeDetails["parent"] = parentID
            nodeDetails["uniqueID"] = uniqueProjectID
            nodeDetails["projectName"] = childProject["name"]
            nodeDetails["projectLink"] = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(childProject["id"]) + "&tab=projectInventory"

            projectList.append( nodeDetails )

            create_project_hierarchy(childProject, uniqueProjectID, projectList, baseURL)

    return projectList
