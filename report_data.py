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

    reportOptions = reportData["reportOptions"]
    primaryProjectID = reportData["primaryProjectID"]
    secondaryProjectID = reportData["secondaryProjectID"]
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
    secondaryProjectList, secondaryProjectInventoryData = get_project_details(baseURL, authToken, secondaryProjectID, reportData)
    secondaryProjectName = secondaryProjectList[0]["projectName"]

    
    # How much space will be required for the hierarchies display?
    if len(secondaryProjectList) > largestHierachy:
        largestHierachy = len(secondaryProjectList)

    setPrimaryProjectInventoryData = set(primaryProjectInventoryData)
    setSecondaryProjectInventoryData = set(secondaryProjectInventoryData)

    commonComponents = list((setPrimaryProjectInventoryData).intersection(setSecondaryProjectInventoryData))
    uniquePrimaryProject_C = list((setPrimaryProjectInventoryData).difference(setSecondaryProjectInventoryData))
    uniqueSecondaryProject_C = list((setSecondaryProjectInventoryData).difference(setPrimaryProjectInventoryData))

    # Get data for the components that are in common to both reports
    for componentId in commonComponents:
        componentName = primaryProjectInventoryData[componentId]["componentName"]
        tableRows = compare_CV(componentName, primaryProjectInventoryData[componentId], secondaryProjectInventoryData[componentId])

        for tableRow in tableRows:
            # Based on the results determine the matchType      
            primaryProjectVersion =    tableRow[1] 
            primaryProjectLicense =    tableRow[2] 
            primaryProjectPublicationState =   tableRow[4] 
            secondaryProjectVersion =   tableRow[5] 
            secondaryProjectLicense =  tableRow[6] 
            secondatryProjectPublicationState =  tableRow[8] 

            matchType = "C" # At a bare minimum the components match here

            if primaryProjectVersion == secondaryProjectVersion:
                matchType += "V"
            if primaryProjectLicense == secondaryProjectLicense:
                matchType += "L"
            if primaryProjectPublicationState == secondatryProjectPublicationState:
                matchType += "P"


            tableRow.append(matchType)
            tableData.append(tableRow)
    
    # Get data for the components that are unique to the primary project
    for component in uniquePrimaryProject_C:
        matchType = "uniquePrimaryProject"
        componentName = primaryProjectInventoryData[component]["componentName"]
        partialRows = process_unique_component(primaryProjectInventoryData[component]["componentVersions"])

        if "errorMsg" in partialRows:
            return {"errorMsg", "%s for %s - %s" %(partialRows["errorMsg"], component, componentName)}
        
        for partialRow in partialRows:
            tableRow = [componentName] + partialRow + [None, None, None, None, matchType]
            tableData.append(tableRow)

    # Get data for the components that are unique to the secondary project
    for component in uniqueSecondaryProject_C:
        matchType = "uniqueSecondaryProject"
        componentName = secondaryProjectInventoryData[component]["componentName"]
        partialRows = process_unique_component(secondaryProjectInventoryData[component]["componentVersions"])

        if "errorMsg" in partialRows:
            return {"errorMsg", "%s for %s - %s" %(partialRows["errorMsg"], component, componentName)}

        for partialRow in partialRows:
            tableRow = [componentName, None, None, None, None] + partialRow + [matchType]
            tableData.append(tableRow)

    # Sort the information by the component name
    tableData = sorted(tableData, key=lambda x: x[0])

    reportData["primaryProjectName"] = primaryProjectName
    reportData["primaryProjectList"] = primaryProjectList
    reportData["secondaryProjectName"] = secondaryProjectName
    reportData["secondaryProjectList"] = secondaryProjectList
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

            # Cycle through each item to get the CVL data
            for inventoryItem in projectInventoryResponse:

                componentId = inventoryItem["componentId"]
                componentName = inventoryItem["componentName"]
                componentVersionName = inventoryItem["componentVersionName"]
                selectedLicenseId = inventoryItem["selectedLicenseId"]
                selectedLicense = inventoryItem["selectedLicenseSPDXIdentifier"] 
                              
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
                                inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState].append(projectName)
                            else:
                                inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState] = []
                                inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState].append(projectName)
                        else:
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense] = {}
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"] = {}
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState] = []
                            inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState].append(projectName)
                    else:
                        inventoryData[componentId]["componentVersions"][componentVersionName] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"] = {}
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState] = []
                        inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState].append(projectName)
                else:
                    inventoryData[componentId] = {}  # A dictionary using comp version as keys
                    inventoryData[componentId]["componentName"] = componentName
                    inventoryData[componentId]["componentVersions"] = {}  # A dictionary using selected license as keys
                    inventoryData[componentId]["componentVersions"][componentVersionName] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"] = {}
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState] = []
                    inventoryData[componentId]["componentVersions"][componentVersionName]["licenses"][selectedLicense]["publishedState"][publishedState].append(projectName)


    return projectList, inventoryData


#------------------------------------------
def compare_CV(componentName, primaryProject_C_Data, secondaryProject_C_Data):
    print("    Compare versions for %s" %componentName)
    tableRows = []
    primaryProject_CV_Data = primaryProject_C_Data["componentVersions"]
    secondaryProject_CV_Data = secondaryProject_C_Data["componentVersions"]

    setPrimaryProject_CV_Data = set(primaryProject_CV_Data)
    setSecondaryProject_CV_Data = set(secondaryProject_CV_Data)

    common_CV = list((setPrimaryProject_CV_Data).intersection(setSecondaryProject_CV_Data))
    uniquePrimaryCV= list((setPrimaryProject_CV_Data).difference(setSecondaryProject_CV_Data))
    uniqueSecondaryCV = list((setSecondaryProject_CV_Data).difference(setPrimaryProject_CV_Data))

    if len(common_CV) == 0:          
        print("        No common versions for: %s" %(componentName))

        if len(primaryProject_CV_Data) ==  len(secondaryProject_CV_Data):
            # There are an equal number of items in both projects
            if len(primaryProject_CV_Data) == 1:
                # Just a simple version change what about the license
                primaryProjectVerion = list(primaryProject_CV_Data.keys())[0]
                secondaryProjectVerion = list(secondaryProject_CV_Data.keys())[0]

                tableRow = compare_CVL(componentName, primaryProject_CV_Data, primaryProjectVerion, secondaryProject_CV_Data, secondaryProjectVerion)
                tableRows.append(tableRow)
                return tableRows
            else:
                return["TODO", "There are mulitiple versions of this component for each project", None, None, None, None, None, None, None]
        else:
            # Different number of versions for each set and none in common and no way to determine if one is an upgrade to
            # another or not so just combine the information into a single row and mark as unreconcilable
            
            matchType = "unreconcilable"
            partialRows = process_unique_component(primaryProject_CV_Data)

            if "errorMsg" in partialRows:
                return {"errorMsg", "%s for %s" %(partialRows["errorMsg"],  componentName)}
            
            for partialRow in partialRows:
                tableRow = [componentName] + partialRow + [None, None, None, None, matchType]
                tableRows.append(tableRow)

            partialRows = process_unique_component(secondaryProject_CV_Data)

            if "errorMsg" in partialRows:
                return {"errorMsg", "%s for %s" %(partialRows["errorMsg"],  componentName)}
            
            for partialRow in partialRows:
                tableRow = [componentName, None, None, None, None] + partialRow + [matchType]
                tableRows.append(tableRow)

            return tableRows

    elif len(common_CV) == 1:  # There is a single common versions match
        version = common_CV[0]
        print("        Exact version match - %s" %common_CV[0])
        tableRow = compare_CVL(componentName, primaryProject_CV_Data, version, secondaryProject_CV_Data, version)
        tableRows.append(tableRow)
        return tableRows
    
    else:  # There are mulitiple common versions for this component
        print("        Multiple common comp/versions")
        return["TODO", " Multiple common comp/versions", None, None, None, None, None, None, None]


  #------------------------------------------
def compare_CVL(componentName, primaryProject_CV_Data, primaryProjectVerion, secondaryProject_CV_Data, secondaryProjectVerion):

    primaryProject_CVL_Data = primaryProject_CV_Data[primaryProjectVerion]["licenses"]
    secondaryProject_CVL_Data = secondaryProject_CV_Data[secondaryProjectVerion]["licenses"]

    print("        Compare licenses for %s : %s vs %s" %(componentName, primaryProjectVerion, secondaryProjectVerion))

    setprimaryProject_CVL_Data = set(primaryProject_CVL_Data)
    setsecondaryProject_CVL_Data = set(secondaryProject_CVL_Data)

    common_CVL = list((setprimaryProject_CVL_Data).intersection(setsecondaryProject_CVL_Data))
    uniquePrimary_CVL = list((setprimaryProject_CVL_Data).difference(setsecondaryProject_CVL_Data))
    uniqueSecondary_CVL = list((setsecondaryProject_CVL_Data).difference(setprimaryProject_CVL_Data))  

    if len(common_CVL) == 0: 
        if len(uniquePrimary_CVL) == len(uniqueSecondary_CVL):
            # Equal number of unique CVL items from each hierarchy
            if len(uniquePrimary_CVL) == 1:
                
                primaryProjectLicense = uniquePrimary_CVL[0]
                secondaryProjectLicense = uniqueSecondary_CVL[0]

                tableRow = compare_CVLP(componentName, primaryProject_CVL_Data, primaryProjectVerion, primaryProjectLicense, secondaryProject_CVL_Data, secondaryProjectVerion, secondaryProjectLicense)

                return tableRow
            else:
                return["TODO", "Multiple license for  %s-%s-%s" %(componentName, primaryProjectVerion, secondaryProjectVerion), None, None, None, None, None, None, None, None]
        else:
            return["TODO", "Unequal quanity of license for %s-%s-%s" %(componentName, primaryProjectVerion, secondaryProjectVerion), None, None, None, None, None, None, None, None]
    

    elif len(common_CVL) == 1:  # Exact match for CVL so need to look at projects and published states
        license = common_CVL[0]
        print("            Exact license match - %s" %license)
 
        tableRow = compare_CVLP(componentName, primaryProject_CVL_Data, primaryProjectVerion, license, secondaryProject_CVL_Data, secondaryProjectVerion, license)
        return tableRow
    else:
        print("            Mutliple common licenses for  %s-%s-%s" %(componentName, primaryProjectVerion, secondaryProjectVerion))
        return["TODO", "Muliple Common Licenses for %s-%s-%s" %(componentName, primaryProjectVerion, secondaryProjectVerion), None, None, None, None, None, None, None, None]


#------------------------------
def compare_CVLP(componentName, primaryProject_CVL_Data, primaryProjectVerion, primaryProjectLicense, secondaryProject_CVL_Data, secondaryProjectVerion, secondaryProjectLicense):

    primaryProject_CVLP_Data = primaryProject_CVL_Data[primaryProjectLicense]["publishedState"]
    secondaryProject_CVLP_Data = secondaryProject_CVL_Data[secondaryProjectLicense]["publishedState"]
       
    print("            Compare published state for %s : %s-%s vs %s-%s" %(componentName, primaryProjectVerion, primaryProjectLicense, secondaryProjectVerion, secondaryProjectLicense))

    setprimaryProject_CVLP_Data = set(primaryProject_CVLP_Data)
    setsecondaryProject_CVLP_Data = set(secondaryProject_CVLP_Data)

    common_CVLP = list((setprimaryProject_CVLP_Data).intersection(setsecondaryProject_CVLP_Data))
    uniquePrimary_CVLP = list((setprimaryProject_CVLP_Data).difference(setsecondaryProject_CVLP_Data))
    uniqueSecondary_CVLP = list((setsecondaryProject_CVLP_Data).difference(setprimaryProject_CVLP_Data))  

    if len(common_CVLP) == 0:          
        if len(uniquePrimary_CVLP) == len(uniqueSecondary_CVLP):
            # Equal number of unique CVL items from each hierarchy
            if len(uniquePrimary_CVLP) == 1:
                
                primaryProjectPublishedState = uniquePrimary_CVLP[0]
                secondaryProjectPublishedState = uniqueSecondary_CVLP[0]

                primaryProjectProjects = primaryProject_CVLP_Data[primaryProjectPublishedState]
                secondaryProjectProjects = secondaryProject_CVLP_Data[secondaryProjectPublishedState]

                tableRow = [componentName, primaryProjectVerion, primaryProjectLicense, primaryProjectProjects, primaryProjectPublishedState, secondaryProjectVerion, secondaryProjectLicense,  secondaryProjectProjects, secondaryProjectPublishedState]
                return tableRow
            
            else:
                return["TODO", "Equal but different counts for published state of %s : %s-%s vs %s-%s" %(componentName, primaryProjectVerion, primaryProjectLicense, secondaryProjectVerion, secondaryProjectLicense), None, None, None, None, None, None, None, None]
        else:
            return["TODO", "Differing counts for published state of %s : %s-%s vs %s-%s" %(componentName, primaryProjectVerion, primaryProjectLicense, secondaryProjectVerion, secondaryProjectLicense), None, None, None, None, None, None, None, None]     

   
    elif len(common_CVLP) == 1:  # Exact match for CVL so need to look at projects and published states
        publishedState = common_CVLP[0]
        primaryProjectProjects = primaryProject_CVLP_Data[publishedState]
        secondaryProjectProjects = secondaryProject_CVLP_Data[publishedState]

        tableRow = [componentName, primaryProjectVerion, primaryProjectLicense, primaryProjectProjects, publishedState, secondaryProjectVerion, secondaryProjectLicense,  secondaryProjectProjects, publishedState]
        return tableRow
    else:
        return["TODO", "Mutliple publication states %s : %s-%s vs %s-%s" %(componentName, primaryProjectVerion, primaryProjectLicense, secondaryProjectVerion, secondaryProjectLicense), None, None, None, None, None, None, None, None]


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
                    projects = licenses[licenseName]["publishedState"][publicationState]
                    partialRows.append([version, licenseName, projects, publicationState])

    return partialRows

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
