'''
Copyright 2020 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Aug 07 2020
File : report_data.py
'''

import logging
import common.project_heirarchy
import common.api.project.get_project_inventory

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, primaryProjectID, authToken, reportData):
    logger.info("Entering gather_data_for_report")

    reportOptions = reportData["reportOptions"]

    # Parse report options
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False
    secondaryProjectID = reportOptions["otherProjectId"]

    inventoryData = {} # Create a dictionary containing the inveotry data using name/version strings as keys
    projectNames = {} # Create a list to contain the project names
    projectData = {}
    largestHierachy = 0

    for projectID in [primaryProjectID, secondaryProjectID]:
        projectList=[]
        projectData[projectID] = {}
        
        # Get the list of parent/child projects start at the base project
        projectList = common.project_heirarchy.create_project_heirarchy(baseURL, authToken, projectID, includeChildProjects)
        topLevelProjectName = projectList[0]["projectName"]

        projectData[projectID]["projectList"] = projectList

        # How much space will be required for the hierarchies display?
        if len(projectList) > largestHierachy:
            largestHierachy = len(projectList)
        

        #  Gather the details for each project and summerize the data
        for project in projectList:

            subProjectID = project["projectID"]
            projectName = project["projectName"]
            projectLink = project["projectLink"]

            # Get details for  project
            try:
                projectInventoryResponse = common.api.project.get_project_inventory.get_project_inventory_details(baseURL, subProjectID, authToken)
            except:
                logger.error("    No project ineventory response!")
                print("No project inventory response.")
                return -1

            projectName = projectInventoryResponse["projectName"]
            projectNames[projectID] = topLevelProjectName
            projectData[projectID]["projectName"] = projectName

            inventoryItems = projectInventoryResponse["inventoryItems"]

            for inventoryItem in inventoryItems:
                componentName = inventoryItem["componentName"]
                componentVersionName = inventoryItem["componentVersionName"]
                selectedLicenseName = inventoryItem["selectedLicenseName"]
                selectedLicenseSPDXIdentifier = inventoryItem["selectedLicenseSPDXIdentifier"]
                componentForgeName = inventoryItem["componentForgeName"]

                if selectedLicenseSPDXIdentifier != "":
                    selectedLicenseName = selectedLicenseSPDXIdentifier

                keyValue = componentName + "-" + componentVersionName
                
                # See if there is already an entry for the same name/version
                if keyValue not in inventoryData:
                    inventoryData[keyValue] = {}

                inventoryData[keyValue][topLevelProjectName] = {
                                                        "projectName" : projectName,
                                                        "projectLink" : projectLink,
                                                        "componentName" : componentName,
                                                        "componentVersionName" : componentVersionName,
                                                        "selectedLicenseName" : selectedLicenseName,
                                                        "componentForgeName" : componentForgeName
                                                    }

    reportData["projectList"] = projectList
    reportData["projectData"] = projectData
    reportData["projectNames"] = projectNames
    reportData["topLevelProjectName"] = topLevelProjectName
    reportData["secondaryProjectID"] = secondaryProjectID
    reportData["inventoryData"] = inventoryData
    reportData["largestHierachy"] = largestHierachy

    logger.info("Exiting gather_data_for_report")

    return reportData

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
