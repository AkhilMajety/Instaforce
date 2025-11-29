from langchain_community.document_loaders import TextLoader
from simple_salesforce import Salesforce


def main():
    print("Hello from instaforce!")

    # Login
    sf = Salesforce(username='er.akhilmajety@cunning-hawk-qwml06.com',
                    password='Ind@2025',
                    security_token='JIiQYd3zL5toRr17pNjuCae4')
    
    apex_body = """
public with sharing class DemoClass {
    public static String hello() {
        return 'Hello from AI!';
    }
}
"""

    result = sf.Tooling.ApexClass.create({
    "Name": "DemoClass",
    "Body": apex_body
})

    print(result)
# Call Apex REST service (assuming you exposed your Apex class as a REST endpoint)
    # sf.Contact.create({'LastName':'Rudra','Email':'Rudra@example.com'})
   # mdapi = sf.mdapi


    # mdapi.ApexClass.create(new_class)


#, {http://soap.sforce.com/2006/04/metadata}ApexClass,
    # custom_object = mdapi.CustomObject(
    # fullName = "Inception__c",
    # label = "Inception",
    # pluralLabel = "Inceptions",
    # nameField = mdapi.CustomField(
    #     label = "GT",
    #     type = mdapi.FieldType("Text")
    # ),
    # deploymentStatus = mdapi.DeploymentStatus("Deployed"),
    # sharingModel = mdapi.SharingModel("Read")
    # )

  #  mdapi.CustomObject.create(custom_object)
   # print('deploymentStatus' ,deploymentStatus)








if __name__ == "__main__":
    main()
