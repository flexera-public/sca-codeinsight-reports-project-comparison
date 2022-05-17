'''
Copyright 2020 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Aug 07 2020
File : report_data.py
'''

import logging
import CodeInsight_RESTAPIs.project.get_project_inventory
import CodeInsight_RESTAPIs.project.get_child_projects

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, primaryProjectID, reportOptions, authToken, reportName):
    logger.info("Entering gather_data_for_report")

    # Parse report options
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False
    secondaryProjectID = reportOptions["otherProjectId"]

    
    projectList = {} # Dictionary of lists to hold parent/child details for report
    inventoryData = {} # Create a dictionary containing the inveotry data using name/version strings as keys
    projectNames = {} # Create a list to contain the project names
    projectData = {}
    largestHierachy = 0

    for projectID in [primaryProjectID, secondaryProjectID]:
        projectList=[]
        projectData[projectID] = {}

        
        # Get the list of parent/child projects start at the base project
        projectHierarchy = CodeInsight_RESTAPIs.project.get_child_projects.get_child_projects_recursively(baseURL, projectID, authToken)
        topLevelProjectName = projectHierarchy["name"]

        # Create a list of project data sorted by the project name at each level for report display  
        # Add details for the parent node
        nodeDetails = {}
        nodeDetails["parent"] = "#"  # The root node
        nodeDetails["projectName"] = projectHierarchy["name"]
        nodeDetails["projectID"] = projectHierarchy["id"]
        nodeDetails["projectLink"] = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(projectHierarchy["id"]) + "&tab=projectInventory"

        projectList.append(nodeDetails)

        if includeChildProjects == "true":
            projectList = create_project_hierarchy(projectHierarchy, projectHierarchy["id"], projectList, baseURL)
        else:
            logger.debug("Child hierarchy disabled")

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
                projectInventoryResponse = CodeInsight_RESTAPIs.project.get_project_inventory.get_project_inventory_details(baseURL, subProjectID, authToken)
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

    reportData = {}
    reportData["reportName"] = reportName
    reportData["projectData"] = projectData
    reportData["projectNames"] = projectNames
    reportData["projectID"] = primaryProjectID
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
