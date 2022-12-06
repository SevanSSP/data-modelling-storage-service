Feature: Explorer - Add file

  Background: There are data sources in the system
    Given the system data source and SIMOS core package are available
    Given there are data sources
      | name             |
      | test-DS |

    Given there are repositories in the data sources
      | data-source | host | port  | username | password | tls   | name      | database  | collection | type     | dataTypes |
      | test-DS     | db   | 27017 | maf      | maf      | false | repo1     |  bdd-test | documents  | mongo-db | default   |
      | test-DS     | db   | 27017 | maf      | maf      | false | blob-repo |  bdd-test | test       | mongo-db | blob      |


    Given there exist document with id "1" in data source "test-DS"
    """
    {
        "name": "root_package",
        "description": "",
        "type": "sys://system/SIMOS/Package",
        "isRoot": true,
        "content": [
            {
                "_id": "2",
                "name": "MultiplePdfContainer",
                "type": "sys://system/SIMOS/Blueprint"
            },
            {
                "_id": "3",
                "name": "BaseChild",
                "type": "sys://system/SIMOS/Blueprint"
            },
            {
                "_id": "4",
                "name": "Parent",
                "type": "sys://system/SIMOS/Blueprint"
            },
            {
                "_id": "5",
                "name": "SpecialChild",
                "type": "sys://system/SIMOS/Blueprint"
            },
            {
                "_id": "6",
                "name": "parentEntity",
                "type": "sys://test-DS/root_package/Parent"
            },
            {
                "_id": "7",
                "name": "Hobby",
                "type": "sys://system/SIMOS/Blueprint"
            },
            {
                "_id": "8",
                "name": "Comment",
                "type": "sys://system/SIMOS/Blueprint"
            }
        ]
    }
    """
    Given there exist document with id "2" in data source "test-DS"
    """
    {
      "type": "sys://system/SIMOS/Blueprint",
      "name": "MultiplePdfContainer",
      "description": "A recursive blueprint with multiple PDFs",
      "attributes": [
        {
          "attributeType": "string",
          "type": "sys://system/SIMOS/BlueprintAttribute",
          "name": "name"
        },
        {
          "attributeType": "string",
          "type": "sys://system/SIMOS/BlueprintAttribute",
          "name": "description"
        },
        {
          "attributeType": "string",
          "type": "sys://system/SIMOS/BlueprintAttribute",
          "name": "type",
          "default": "blueprints/root_package/RecursiveBlueprint"
        },
        {
          "name": "a_pdf",
          "attributeType": "sys://system/SIMOS/blob_types/PDF",
          "type": "sys://system/SIMOS/BlueprintAttribute"
        },
        {
          "name": "another_pdf",
          "attributeType": "sys://system/SIMOS/blob_types/PDF",
          "type": "sys://system/SIMOS/BlueprintAttribute"
        },
        {
          "name": "pdf_container",
          "attributeType": "sys://test-DS/root_package/MultiplePdfContainer",
          "type": "sys://system/SIMOS/BlueprintAttribute",
          "optional": true
        }
      ]
    }
    """

    Given there exist document with id "3" in data source "test-DS"
    """
    {
      "type": "sys://system/SIMOS/Blueprint",
      "name": "BaseChild",
      "description": "",
      "extends": ["sys://system/SIMOS/NamedEntity"],
      "attributes": [
        {
        "name": "AValue",
        "attributeType": "integer",
        "type": "sys://system/SIMOS/BlueprintAttribute"
        }
      ]
    }
    """


    Given there exist document with id "4" in data source "test-DS"
    """
    {
      "type": "sys://system/SIMOS/Blueprint",
      "name": "Parent",
      "description": "",
      "extends": ["sys://system/SIMOS/NamedEntity"],
      "attributes": [
        {
        "name": "SomeChild",
        "attributeType": "sys://test-DS/root_package/BaseChild",
        "type": "sys://system/SIMOS/BlueprintAttribute",
        "optional": true
        }
      ]
    }
    """

    Given there exist document with id "5" in data source "test-DS"
    """
    {
      "type": "sys://system/SIMOS/Blueprint",
      "name": "SpecialChild",
      "description": "",
      "extends": ["sys://test-DS/root_package/BaseChild"],
      "attributes": [
        {
          "name": "AnExtraValue",
          "attributeType": "string",
          "type": "sys://system/SIMOS/BlueprintAttribute"
        },
        {
          "name": "Hobbies",
          "attributeType": "sys://test-DS/root_package/Hobby",
          "type": "sys://system/SIMOS/BlueprintAttribute",
          "optional": true,
          "dimensions": "*"
        }
      ]
    }
    """


  Given there exist document with id "6" in data source "test-DS"
    """
    {
      "type": "sys://test-DS/root_package/Parent",
      "name": "parentEntity",
      "description": "",
      "SomeChild": {}
    }
    """

  Given there exist document with id "7" in data source "test-DS"
    """
    {
      "type": "sys://system/SIMOS/Blueprint",
      "name": "Hobby",
      "description": "",
      "extends": ["sys://system/SIMOS/NamedEntity"],
      "attributes": [
        {
        "name": "difficulty",
        "attributeType": "string",
        "type": "sys://system/SIMOS/BlueprintAttribute"
        }
      ]
    }
    """

  Given there exist document with id "8" in data source "test-DS"
    """
    {
      "type": "sys://system/SIMOS/Blueprint",
      "name": "Comment",
      "description": "a comment blueprint, that does not require a name",
      "attributes": [
        {
        "name": "text",
        "attributeType": "string",
        "type": "sys://system/SIMOS/BlueprintAttribute"
        }
      ]
    }
    """

  Scenario: Add file - attribute for parentEntity
    Given i access the resource url "/api/v1/documents/test-DS/6.SomeChild"
    When i make a "POST" request
    """
    {
      "name": "baseChildInParentEntity",
      "type": "sys://test-DS/root_package/BaseChild",
      "description": "base child in parent",
      "AValue": 0
    }
    """
    Then the response status should be "OK"
    Given I access the resource url "/api/v1/documents/test-DS/6"
    When I make a "GET" request
    Then the response status should be "OK"
    And the response should contain
    """
    {
          "_id": "6",
          "name": "parentEntity",
          "type": "sys://test-DS/root_package/Parent",
          "description": "",
          "SomeChild":
          {
            "name": "baseChildInParentEntity",
            "type": "sys://test-DS/root_package/BaseChild",
            "description": "base child in parent",
            "AValue": 0
          }
    }
    """

  Scenario: Add file (rootPackage) to root of data_source
    Given i access the resource url "/api/v1/documents/test-DS"
    When i make a "POST" request
    """
    {
      "name": "newRootPackage",
      "type": "sys://system/SIMOS/Package",
      "isRoot": true,
      "content": []
    }
    """
    Then the response status should be "OK"

  Scenario: Add file with wrong subtype to parent entity
    Given i access the resource url "/api/v1/documents/test-DS/6.SomeChild"
    When i make a "POST" request
    """
    {
      "name": "hobbynumber1",
      "type": "sys://test-DS/root_package/Hobby",
      "description": "example hobby",
      "difficulty": "high"
    }
    """
    Then the response status should be "Bad Request"
    Given I access the resource url "/api/v1/documents/test-DS/6"
    When I make a "GET" request
    Then the response status should be "OK"
    And the response should contain
    """
    {
          "_id": "6",
          "name": "parentEntity",
          "type": "sys://test-DS/root_package/Parent",
          "description": "",
          "SomeChild": {}
    }
    """

  Scenario: Add file with an extended type to parent entity
    Given i access the resource url "/api/v1/documents/test-DS/6.SomeChild"
    When i make a "POST" request
    """
    {
      "name": "specialChild",
      "type": "sys://test-DS/root_package/SpecialChild",
      "description": "specialized child",
      "AValue": 39,
      "AnExtraValue": "abc",
      "Hobbies": [
        {
          "name": "Football",
          "type": "sys://test-DS/root_package/Hobby",
          "description": "sport",
          "difficulty": "high"
        }
      ]
    }
    """
    Then the response status should be "OK"
    Given I access the resource url "/api/v1/documents/test-DS/6"
    When I make a "GET" request
    Then the response status should be "OK"
    And the response should contain
    """
    {
          "_id": "6",
          "name": "parentEntity",
          "type": "sys://test-DS/root_package/Parent",
          "description": "",
          "SomeChild":
          {
            "name": "specialChild",
            "type": "sys://test-DS/root_package/SpecialChild",
            "description": "specialized child",
            "AValue": 39,
            "AnExtraValue": "abc"
          }
    }
    """

  Scenario: Add file - not contained
    Given i access the resource url "/api/v1/documents/test-DS/1.content?update_uncontained=True"
    When i make a "POST" request
    """
    {
      "name": "new_document",
      "type": "sys://system/SIMOS/Blueprint"
    }
    """
    Then the response status should be "OK"
    Given I access the resource url "/api/v1/documents/test-DS/1"
    When I make a "GET" request
    Then the response status should be "OK"
    And the response should contain
    """
    {
          "name":"root_package",
          "type":"sys://system/SIMOS/Package",
          "content":[
            {
              "name": "MultiplePdfContainer"
            },
            {
              "name":"BaseChild"
            },
            {
              "name":"Parent"
            },
            {
              "name":"SpecialChild"
            },
            {
              "name": "parentEntity"
            },
            {
              "name":"Hobby"
            },
            {
              "name":"Comment"
            },
            {
              "name": "new_document"
            }
          ],
          "isRoot":true
    }
    """

  Scenario: Add file with missing parameters should fail
    Given i access the resource url "/api/v1/documents/test-DS/6.whatever"
    When i make a "POST" request
    """
    {}
    """
    Then the response status should be "Bad Request"
    And the response should be
    """
    {
    "status": 400,
    "type": "BadRequestException",
    "message": "Every entity must have a 'type' attribute",
    "debug": "Unable to complete the requested operation with the given input values.",
    "data": null
    }
    """

  Scenario: Add file to parent that does not exists
    Given i access the resource url "/api/v1/documents/test-DS/-1.documents"
    When i make a "POST" request
    """
    {
      "name": "new_document",
      "type": "sys://system/SIMOS/Blueprint"
    }
    """
    Then the response status should be "Not Found"
    And the response should be
    """
    {
    "status": 404,
    "type": "NotFoundException",
    "message": "Document with id '-1' was not found in the 'test-DS' data-source",
    "debug": "The requested resource could not be found",
    "data": null
    }
    """

  Scenario: Add file to parent with missing permissions on parent
    Given AccessControlList for document "1" in data-source "test-DS" is
    """
    {
      "owner": "someoneElse",
      "others": "READ"
    }
    """
    Given the logged in user is "johndoe" with roles "a"
    Given authentication is enabled
    Given i access the resource url "/api/v1/documents/test-DS/1.content"
    When i make a "POST" request
    """
    {
      "name": "new_document",
      "type": "sys://system/SIMOS/Blueprint"
    }
    """
    Then the response status should be "Forbidden"
    And the response should be
    """
    {
    "status": 403,
    "type": "MissingPrivilegeException",
    "message": "The requested operation requires 'WRITE' privileges",
    "debug": "Action denied because of insufficient permissions",
    "data": null
    }
    """

  Scenario: Add file with duplicate name
    Given i access the resource url "/api/v1/documents/test-DS/root_package/add-to-path"
    When i make a "POST" request with "1" files
    """
      {
        "document": {
          "type": "sys://test-DS/root_package/Parent",
          "name": "parentEntity",
          "description": "",
          "SomeChild": {}
        }
      }
    """
    Then the response status should be "Bad Request"
    And the response should be
    """
    {
    "status": 400,
    "type": "BadRequestException",
    "message": "The document 'test-DS/root_package/parentEntity' already exists",
    "debug": "Unable to complete the requested operation with the given input values.",
    "data": null
    }
    """

  Scenario: Add Comment entity without a name attribute with add-raw endpoint
    Given i access the resource url "/api/v1/documents/test-DS/add-raw"
    When i make a "POST" request
    """
    {
        "_id": "429cb3da-ebbe-4ea6-80a6-b6bca0f67aaa",
        "type": "sys://test-DS/root_package/Comment",
        "description": "comment entity with no name",
        "text": "example comment"
    }
    """
    Then the response status should be "OK"

  Scenario: Add Parent entity without a name attribute with add-to-path endpoint
    Given i access the resource url "/api/v1/documents/test-DS/root_package/add-to-path?update_uncontained=True"
    When i make a "POST" request with "1" files
    """
    {
      "document": {
        "type": "sys://test-DS/root_package/Parent",
        "description": "parent entity with no name"
      }
    }
    """
    Then the response status should be "Unprocessable Entity"
    And the response should be
    """
    {
    "status": 422,
    "type": "ValidationException",
    "message": "Required attribute 'name' not found in the entity",
    "debug": "Values are invalid for requested operation.",
    "data": null
    }
    """

  Scenario: Adding file with id set to empty string should generate new uid
    Given I access the resource url "/api/v1/documents/test-DS/root_package/add-to-path"
    When i make a "POST" request with "1" files
    """
    {
      "document": {
        "_id": "",
        "type":"sys://system/SIMOS/Blueprint",
        "name": "new_bp",
        "description": "Blueprint with no name"
      }
    }
    """
    Then the response status should be "OK"
    And the response should have valid uid

  Scenario: Adding file with id
    Given I access the resource url "/api/v1/documents/test-DS/root_package/add-to-path"
    When i make a "POST" request with "1" files
    """
    {
      "document": {
        "_id": "2283c9b0-d509-46c9-a153-94c79f4d7b7b",
        "type":"sys://system/SIMOS/Blueprint",
        "name": "new_bp",
        "description": "Blueprint with no name"
      }
    }
    """
    Then the response status should be "OK"
    And the response should have valid uid

  Scenario: Add Comment entity without a name attribute with add-to-path endpoint
    Given i access the resource url "/api/v1/documents/test-DS/root_package/add-to-path?update_uncontained=True"
    When i make a "POST" request with "1" files
    """
    {
      "document":
      {
        "type": "sys://test-DS/root_package/Comment",
        "description": "comment entity with no name",
        "text": "example comment"
      }
    }
    """
    Then the response status should be "OK"

  Scenario: Add blueprint without a name attribute with add-to-path endpoint should fail
    Given i access the resource url "/api/v1/documents/test-DS/root_package/add-to-path?update_uncontained=True"
    When i make a "POST" request with "1" files
    """
    {
      "document":
      {
        "type":"sys://system/SIMOS/Blueprint",
        "description": "Blueprint with no name"
      }
    }
    """
    Then the response status should be "Unprocessable Entity"
    And the response should be
    """
    {
    "status": 422,
    "type": "ValidationException",
    "message": "Required attribute 'name' not found in the entity",
    "debug": "Values are invalid for requested operation.",
    "data": null
    }
    """

  Scenario: Add package without a name attribute with add-to-path endpoint should fail
    Given i access the resource url "/api/v1/documents/test-DS/root_package/add-to-path?update_uncontained=True"
    When i make a "POST" request with "1" files
    """
    {
      "document":
      {
        "type":"sys://system/SIMOS/Package",
        "description": "Package with no name"
      }
    }
    """
    Then the response status should be "Unprocessable Entity"
    And the response should be
    """
    {
    "status": 422,
    "type": "ValidationException",
    "message": "Required attribute 'name' not found in the entity",
    "debug": "Values are invalid for requested operation.",
    "data": null
    }
    """

  Scenario: Add parent entity without a name attribute with add_by_parent_id endpoint
    Given i access the resource url "/api/v1/documents/test-DS/1.content?update_uncontained=True"
    When i make a "POST" request
    """
    {
      "type": "sys://test-DS/root_package/Parent",
      "description": "parent entity with no name"
    }
    """
    Then the response status should be "Unprocessable Entity"
    And the response should be
    """
    {
    "status": 422,
    "type": "ValidationException",
    "message": "Required attribute 'name' not found in the entity",
    "debug": "Values are invalid for requested operation.",
    "data": null
    }
    """

  Scenario: Add comment entity without a name attribute with add_by_parent_id endpoint
    Given i access the resource url "/api/v1/documents/test-DS/1.content?update_uncontained=True"
    When i make a "POST" request
    """
    {
      "type": "sys://test-DS/root_package/Comment",
      "description": "comment entity with no name",
      "text": "example comment"
    }
    """
    Then the response status should be "OK"

  Scenario: Add blueprint without a name using add_by_parent_id endpoint should fail
    Given i access the resource url "/api/v1/documents/test-DS/1.content"
    When i make a "POST" request
    """
    {
      "type":"sys://system/SIMOS/Blueprint",
      "description": "Blueprint with no name"
    }
    """
    Then the response status should be "Unprocessable Entity"
    And the response should be
    """
    {
    "status": 422,
    "type": "ValidationException",
    "message": "Required attribute 'name' not found in the entity",
    "debug": "Values are invalid for requested operation.",
    "data": null
    }
    """

  Scenario: Add package without a name using add_by_parent_id endpoint should fail
    Given i access the resource url "/api/v1/documents/test-DS/1.content"
    When i make a "POST" request
    """
    {
      "type":"sys://system/SIMOS/Package",
      "description": "Package with no name"
    }
    """
    Then the response status should be "Unprocessable Entity"
    And the response should be
    """
    {
    "status": 422,
    "type": "ValidationException",
    "message": "Required attribute 'name' not found in the entity",
    "debug": "Values are invalid for requested operation.",
    "data": null
    }
    """

  Scenario: Add file with multiple PDFs
    Given i access the resource url "/api/v1/documents/test-DS/root_package/add-to-path?update_uncontained=True"
    When i make a "POST" request with "4" files
    """
    {
      "document": {
        "name": "new_pdf_container",
        "type": "sys://test-DS/root_package/MultiplePdfContainer",
        "description": "",
        "a_pdf": {
          "name": "MyPDF1",
          "description": "",
          "type": "sys://system/SIMOS/blob_types/PDF",
          "blob": {
            "name": "file1",
            "type": "sys://system/SIMOS/Blob",
            "_blob_id": ""
          },
          "author": "Stig Oskar"
        },
        "another_pdf": {
          "name": "MyPDF2",
          "description": "",
          "type": "sys://system/SIMOS/blob_types/PDF",
          "blob": {
            "name": "file2",
            "type": "sys://system/SIMOS/Blob",
            "_blob_id": ""
          },
          "author": "Stig Oskar"
        },
        "pdf_container": {
          "name": "second_pdf_container",
          "type": "sys://test-DS/root_package/MultiplePdfContainer",
          "description": "",
          "a_pdf": {
            "name": "MyPDF3",
            "description": "",
            "type": "sys://system/SIMOS/blob_types/PDF",
            "blob": {
              "name": "file3",
              "type": "sys://system/SIMOS/Blob",
              "_blob_id": ""
            },
            "author": "Stig Oskar"
          },
          "another_pdf": {
            "name": "MyPDF4",
            "description": "",
            "type": "sys://system/SIMOS/blob_types/PDF",
            "blob": {
              "name": "file4",
              "type": "sys://system/SIMOS/Blob",
              "size": 0,
              "_blob_id": ""
            },
            "author": "Stig Oskar"
          },
          "pdf_container": {}
        }
      }
    }
    """
    Then the response status should be "OK"