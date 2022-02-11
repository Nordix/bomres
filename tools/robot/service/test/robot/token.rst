# Robot Test


## User and Service Authorization Use Case

| **Use Case ID**  | **Use Case Title**                          | **Compliance** | **Test Case**                              |
| ---------------- | ------------------------------------------- | -------------- | ------------------------------------------ |
| IAM.AUTHZ.1      | Service-to-service Authorization by OAuth2  |                | Post Request With Client Credentials grant |



.. code:: robotframework

    *** Settings ***
    Library    RequestsLibrary
    Library    Collections
    
    *** Variables ***
    ${token_endpoint}    https://lb.t2data.com
    ${path}              /resolver/alpine/v1/token
    
    ${client_id}         dummy
    ${client_secret}     qwerty
    

    *** Test Cases ***
    Post Request With Client Credentials grant
         Create Session   baseUri   ${token_endpoint}      verify=False
         &{data}=   Create Dictionary   client_id=${client_id}   client_secret=${client_secret}   grant_type=client_credentials
         &{headers}=  Create Dictionary   Content-Type=application/x-www-form-urlencoded
         ${resp}=   Post Request   baseUri   ${path}   ${data}   headers=${headers}
         Status Should Be  200    ${resp}
         Log  ${resp.status_code}
         Log  ${resp.headers}
         Log  ${resp.content}
         ${access_token}=    Collections.Get From Dictionary    ${resp.json()}    access_token
         Log  ${access_token}
         Set Global Variable      ${access_token} 
    
