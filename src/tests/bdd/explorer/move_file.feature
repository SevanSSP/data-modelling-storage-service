@skip
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

    Given there are documents for the data source "data-source-name" in collection "documents"
      | uid | parent_uid | name         | description | type                   |
      | 1   |            | root_package |             | system/SIMOS/Package     |
      | 2   | 1          | document_1   |             | system/SIMOS/Blueprint |

  # TODO: this only works from withing same data source
  Scenario: Move file (renaming)
    Given i access the resource url "/api/v1/explorer/move-file"
    And data modelling tool templates are imported
    When i make a "PUT" request
    """
    {
      "source": "data-source-name/root_package/document_1",
      "destination": "data-source-name/root_package/document_2"
    }
    """
    Then the response status should be "OK"
    And the response should contain
    """
    {
      "data" : {
        "name": "document_2"
      }
    }
    """