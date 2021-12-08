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

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, project2ID, authToken, reportName):
    logger.info("Entering gather_data_for_report")


    # Create a dictionary containing the inveotry data using name/version strings as keys
    inventoryData = {}
    # Create a list to contain the project names
    projectNames = {}

    for project in [projectID, project2ID]:
        # Get details for  project
        try:
            projectInventoryResponse = CodeInsight_RESTAPIs.project.get_project_inventory.get_project_inventory_details(baseURL, project, authToken)
        except:
            logger.error("    No project ineventory response!")
            print("No project inventory response.")
            return -1

        projectName = projectInventoryResponse["projectName"]
        projectNames[project] = projectName

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

            inventoryData[keyValue][projectName] = {
                                                    "componentName" : componentName,
                                                    "componentVersionName" : componentVersionName,
                                                    "selectedLicenseName" : selectedLicenseName,
                                                    "componentForgeName" : componentForgeName
                                                }


    reportData = {}
    reportData["reportName"] = reportName
    reportData["projectNames"] = projectNames
    reportData["projectID"] = projectID
    reportData["inventoryData"] = inventoryData

    logger.info("Exiting gather_data_for_report")

    return reportData


