*** Settings ***
Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote


Suite Setup  Suite Setup
Suite Teardown  Close All Browsers


*** Test Cases ***

Test Creator Criterion
    Enable autologin as  Contributor
    Create Content  type=Document  title=Site owner document
    ...  id=site-owner-document  container=${test-folder-path}
    Disable autologin
    Enable autologin as  Site Administrator
    Create Content  type=Document  title=Site Administrator document  
    ...  container=${test-folder-path}
    Create Collection  Creator Criterion Collection

    Click Edit In Edit Bar
    Set Creator Criterion To  Site Administrator

    Page should not contain  Site owner document
    Page should contain  Site Administrator document

Test Relative Location Criterion
    Enable autologin as  Site Administrator
    Create Content  type=Document  title=Document outside My Folder
    ...  id=outside-my-folder  container=${test-folder-path}
    Create Content  type=Folder  title=My Folder  id=my-folder  
    ...  container=${test-folder-path}
    Create Content  type=Document  title=Document inside My Folder  
    ...  id=inside-my-folder  container=${test-folder-path}/my-folder
    Create Collection  Location Criteria Collection

    Click Edit In Edit Bar
    Set Relative Location Criterion To  ../my-folder/

    Page should contain  Document inside My Folder
    Page should not contain  Document outside My Folder

Test Review state Criterion
    Enable autologin as  Site Administrator
    ${uid} =  Create Content  type=Document  title=Published Document
    ...  id=published-document  container=${test-folder-path}
    Fire transition  ${uid}  publish
    Create Content  type=Document  title=Private Document 
    ...  id=private-document  container=${test-folder-path}
    Create Collection  My Collection

    Click Edit In Edit Bar
    Set Review state Criterion

    Page should contain  Published Document
    Page should not contain  Private Document

*** Variables ***

${FOLDER_ID}  a-folder
${DOCUMENT_ID}  a-document
${test-folder}  ${PLONE_URL}/test-folder
${test-folder-path}  /plone/test-folder

*** Keywords ***
Suite Setup
    Open test browser
    Go to  ${PLONE_URL}

Suite Teardown
    Close All Browsers

Live Preview number of results should be
    [Arguments]  ${number}
    Wait Until Page Contains  ${number} items matching your search terms.

Live Preview should contain
    [Arguments]  ${title}
    Page should contain  ${title}

Create Collection
    [Arguments]  ${title}
    Go to  ${test-folder}/portal_factory/Collection/dummy_collection/edit
    Input text  name=title  ${title}
    Click Button  Save

Set Creator Criterion To
    [Arguments]  ${creator_criterion}
    Wait Until Page Contains Element  xpath=//select[@name="addindex"]
    Select From List  xpath=//select[@name="addindex"]  Creator
    Wait Until Page Contains Element  xpath=//select[@class='queryoperator']
    Select From List  xpath=//select[@class='queryoperator']  Current logged in user
    Click Button  Save

Set Relative Location Criterion To
    [Arguments]  ${relative_path_criterion}
    Wait Until Page Contains Element  xpath=//select[@name="addindex"]
    Select From List  xpath=(//select[@name="addindex"])[last()]  Location
    Wait Until Page Contains Element  xpath=//select[@class='queryoperator']
    Select From List  xpath=(//select[@class='queryoperator'])[last()]  Relative path
    Wait Until Page Contains Element  xpath=//input[@name="query.v:records"]
    Input Text  xpath=(//input[@name="query.v:records"])[last()]  ${relative_path_criterion}
    Click Button  Save

Set Review state Criterion
    Wait Until Page Contains Element  xpath=//select[@name="addindex"]
    Select From List  xpath=//select[@name="addindex"]  Review state
    Wait Until Page Contains Element  xpath=//select[@class='queryoperator']
    Select Checkbox  xpath=//div[@class='criteria']//dl//input[@value='published']
    Live Preview number of results should be  1
    Live Preview should contain  Published Document
    Click Button  Save


