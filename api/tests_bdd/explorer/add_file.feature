Feature: Explorer - Add file

  Background: There are data sources in the system

    Given there are data sources
      | name             |
      | data-source-name |
      | blueprints       |
      | system           |

    Given there are repositories in the data sources
      | data-source      | host | port  | username | password | tls   | name      | database | collection     | type     | dataTypes |
      | data-source-name | db   | 27017 | maf      | maf      | false | repo1     | local    | documents      | mongo-db | default   |
      | SSR-DataSource   | db   | 27017 | maf      | maf      | false | blob-repo | local    | SSR-DataSource | mongo-db | default   |
      | system           | db   | 27017 | maf      | maf      | false | system    | local    | system         | mongo-db | default   |

    Given data modelling tool templates are imported

    Given there are documents for the data source "data-source-name" in collection "documents"
      | uid | parent_uid | name         | description | type               |
      | 1   |            | root_package |             | system/SIMOS/Package |

  Scenario: Add file - not contained
    Given i access the resource url "/api/v1/explorer/data-source-name/add-to-parent"
    When i make a "POST" request
    """
    {
      "name": "new_document",
      "parentId": "1",
      "type": "system/SIMOS/Blueprint",
      "attribute": "content"
    }
    """
    Then the response status should be "OK"
    Given I access the resource url "/api/v1/documents/data-source-name/1"
    When I make a "GET" request
    Then the response status should be "OK"
    And the response should contain
    """
    {
       "blueprint":{
          "name":"Package",
          "type":"system/SIMOS/Blueprint"
       },
       "document":{
          "name":"root_package",
          "type":"system/SIMOS/Package",
          "content":[
            {
              "name":"new_document"
            }
          ],
          "isRoot":true,
          "storageRecipes":[]
       }
    }
    """
  @skip
  Scenario: Add file with missing parameter name should fail
    Given i access the resource url "/api/v1/explorer/data-source-name/add-to-parent"
    When i make a "POST" request
    """
    {
      "parentId": "1",
      "type": "system/SIMOS/Blueprint"
    }
    """
    Then the response status should be "Bad Request"
    And the response should equal
    """
    {"type": "PARAMETERS_ERROR", "message": "name: is missing\nattribute: is missing"}
    """

  @skip
  Scenario: Add file with missing parameters should fail
    Given i access the resource url "/api/v1/explorer/data-source-name/add-to-parent"
    When i make a "POST" request
    """
    {}
    """
    Then the response status should be "Bad Request"
    And the response should equal
    """
    {
      "type": "PARAMETERS_ERROR",
      "message": "parentId: is missing\nname: is missing\ntype: is missing\nattribute: is missing"
    }
    """

  Scenario: Add file to parent that does not exists
    Given i access the resource url "/api/v1/explorer/data-source-name/add-to-parent"
    When i make a "POST" request
    """
    {
      "name": "new_document",
      "parentId": "-1",
      "type": "system/SIMOS/Blueprint",
      "attribute": "documents"
    }
    """
    Then the response status should be "Not Found"
    And the response should equal
    """
    {"type": "RESOURCE_ERROR", "message": "The entity, with id -1 is not found"}
    """
