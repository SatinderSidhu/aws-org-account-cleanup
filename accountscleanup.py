#Python program for AWS Identity store User and Group Management
import argparse
import json
import boto3
import csv


aws_region = 'us-east-1'

client_org =  boto3.client('organizations', 'account')
client_account =  boto3.client('account')
service_catalog = boto3.client('servicecatalog',region_name=aws_region)
client_sso = boto3.client('sso')
client_ssooidc = boto3.client('sso-oidc')

# Update the following default values to your OU values
current_ou = 'Sandbox (ou-tacd-94yat1mt)'
external_ou = 'External (ou-tacd-hrb2mnda)'
suspended_ou = 'Suspended(ou-tacd-24g0dzc3)'
archive_ou = 'Archive (ou-tacd-q2om8496)'

verbose = False


def cleanup_accounts_bulk(args):
    """ 
    This function reads a CSV and and do following things & take various action metioned according to the action
    
    """
    file_name = args.filename
    verbose = args.verbose
    print(' verbose level ', verbose)
    
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        count =1
        for row in reader:
            try:
                awsaccountid = row['awsaccountid']
                action = row['action']
                sourceou = row['sourceou']
                if not sourceou:
                    sourceou = current_ou
                targetou = row['targetou']
                newrootemail = row['newrootemail']
                newaccountname = row['newaccountname']
                changeaccountname = False
                changerootaccountemail = False
                
                # Get account detail 
                response_describe_account = client_org.describe_account(
                    AccountId=awsaccountid
                )

                print(' ---  ')            
                print(' --- [',count,'] AWS Account #',awsaccountid, ' --- ')
                if response_describe_account["Account"]["Status"] != "ACTIVE":
                    print(' AWS Account #',awsaccountid, ' is not ACTIVE --- Its Status is ',response_describe_account["Account"]["Status"])
                    return 0;
                    
                # Continue checking the operation & work accordingly
                aws_account_root_email = response_describe_account["Account"]["Email"]
                aws_account_root_name = response_describe_account["Account"]["Name"]
                if not newaccountname:
                    newaccountname = aws_account_root_name
                    changeaccountname = False
                else:
                    changeaccountname = True
        
                
                print(' ')
                if action == 'external':
                    if not targetou:
                        targetou = external_ou
                    print(' --- [',count,'] AWS Account #',awsaccountid,' Operation EXTERNAL TRANSFER  to ',newrootemail, '--- ')
                    if moveouandupdateawsaccountname(awsaccountid, aws_account_root_email, targetou, newaccountname, changeaccountname) == 1:
                        # updateprimaryemail(awsaccountid, newrootemail)
                        print(' good luck ')
                    
                if action == 'external-org-start':
                    if not targetou:
                        targetou = external_ou
                    print(' --- [',count,'] AWS Account #',awsaccountid,' Operation EXTERNAL TRANSFER  START to ',newrootemail, '--- ')
                    if moveouandupdateawsaccountname(awsaccountid, aws_account_root_email, targetou, newaccountname, changeaccountname) == 1:
                        updateprimaryemail(awsaccountid, newrootemail)
                        print(' SUCCESS ')
    
                if action == 'external-org-finish':
                    if not targetou:
                        targetou = external_ou
                    print(' --- [',count,'] AWS Account #',awsaccountid,' Operation EXTERNAL TRANSFER FINISH ',newrootemail, '--- ')
                    if remove_from_org(awsaccountid) == 1:
                        print(f' SUCCESS ( AWS Account {awsaccountid} has been removed from Organization. Now it can be invited from another organization) ')
                    print(' Please update delete-sso-accounts.csv & execute following command to remove all SSO Accounts ')
                    print(' ---- python3 delete-sso-accounts.py delete_sso_accounts_bulk  --filename delete-sso-accounts.csv --- ')
        
        
    
                if action =='internal':
                    if not targetou:
                        targetou = current_ou
                        
                    print(' --- [',count,'] AWS Account #',awsaccountid,' Operation INTERNAL TRANSFER  -- ')

                    print(' --- [',count,'.1] AWS Account #',awsaccountid,' Operation INTERNAL TRANSFER - [Moving OU to ', targetou,'] -- ')

                    responseintenaloumove = moveouandupdateawsaccountname(awsaccountid, aws_account_root_email, targetou, newaccountname, changeaccountname)
                    print(' --- [',count,'.2] AWS Account #',awsaccountid,' Operation INTERNAL TRANSFER - [Updating the Account name to ', newaccountname,'] -- ')
                    
                    if responseintenaloumove:
                       print(' --- [',count,'.3] AWS Account #',awsaccountid,' Operation INTERNAL TRANSFER - [Change the root email to to ', newrootemail,'] -- ')
                       updateprimaryemail(awsaccountid, newrootemail)
                       print('Success')
                    

                    print(' --- [',count,'.4] AWS Account #',awsaccountid,' Operation INTERNAL TRANSFER - [Deleting any SSO Accounts] -- ')
                    
                    print(' Please update delete-sso-accounts.csv & execute following command to remove all SSO Accounts ')
                    print(' ---- python3 delete-sso-accounts.py delete_sso_accounts_bulk  --filename delete-sso-accounts.csv --- ')

        
    
                if action =='close':

                    print(' --- [',count,'] AWS Account #',awsaccountid,' Operation CLOSE Account  --- ')
                    
                    closeaccount(awsaccountid)
                    if  moveouandupdateawsaccountname(awsaccountid, aws_account_root_email, suspended_ou, newaccountname, changeaccountname) == 1:
                        print(' SUCCESS ' )
                    
                    
                    
                if action =='archive':

                    print(' --- [',count,'] AWS Account #',awsaccountid,' Operation ARCHIVE Account  --- ')
                    if  moveouandupdateawsaccountname(awsaccountid, aws_account_root_email, archive_ou, newaccountname, changeaccountname) == 1:
                        print(' SUCCESS ' )

                count = count+1
            except Exception as e:
                print(' An error has occured in operation ',e)
                return 0
    
    
    
def updateprimaryemail(acountid, primaryemailid):
    """ 
    This function update the primary email id on the AWS account
     
    """
    print('Updating primary email address of Account # ',acountid,' to -> ', primaryemailid)
    
    try:
        response = client_account.start_primary_email_update(
            AccountId=acountid,
            PrimaryEmail=primaryemailid
        )
    
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f'Success - Root email update invitation has been sent to {primaryemailid}');
        
        return 1

    except Exception as e:
        print(' An error has occured in operation ',e)
        return 0
     
def closeaccount(acountid):
    """ 
    This function update the primary email id on the AWS account
    """ 

    print('closing account-> ',acountid)

    try:    
        response = client_org.close_account(
            AccountId=acountid,
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('Success')
            
        return 1

    except Exception as e:
        print(' An error has occured in operation ',e)
        return 0


def moveoprovisionedproduct(aws_account_id, aws_account_root_email, destination_ou_id):
    """ 
    This function move the AWS Account (Provisioned product) from one parent Provsioned product to another )
    We can only move an AWS account from one OU to another, via the provisioned product method. 
    """ 

    provisioned_product = get_provisioned_product_detail(aws_account_id)

    #Guard - Check if the provisioned product is in good state
    # print(provisioned_product)

    if provisioned_product['Status'] =='UNDER_CHANGE':
        print('    Can not perform any operation as the status i', provisioned_product['Status'] )
        return 0

    
    print("-")
    # Get the provisioned product for the account
    provisioned_product_detail = service_catalog.describe_provisioned_product(
        Id=provisioned_product['Id']
    )
    # print(f"  Describe Provision  Product Detail : {provisioned_product_detail}")
    
    
    print("-")
    if provisioned_product:
                
        if provisioned_product:
            print(f"Provisioned Product Record Details:")
            provisioned_product['Id']
            print(f"  Name: {provisioned_product['Name']}")
            print(f"  Id: {provisioned_product['Id']}")
            print(f"  Status: {provisioned_product['Status']}")
            if verbose:
                print(f"  Full Provision  Product Detail : {provisioned_product}")
    
        else:
            print(f"Failed to retrieve provisioned product record details.") 
               
               
        # Set the product ID and provisioning artifact ID for the AWS Organizations product
        propvisioned_product_id = provisioned_product['Id'] 
        product_id = provisioned_product['ProductId'] # 'prod-a6orefazxydq4'  # Replace with the AWS Organizations product ID
        provisioning_artifact_id = provisioned_product['ProvisioningArtifactId']
        provisioning_artifact_name = provisioned_product['ProvisioningArtifactName']

        #try:
            # Check if the account is currently in the source OU
        print(f"Moving AWS Account {aws_account_id}  to {destination_ou_id}")
        # Update the provisioned product to move the account to the destination OU
        
        response = service_catalog.update_provisioned_product(
            ProductId=product_id,
            ProvisionedProductId=propvisioned_product_id,
            ProvisioningArtifactName = provisioning_artifact_name,
            # ProvisioningArtifactId = provisioning_artifact_id,
            PathId= "lpv3-ncl5qh7lqv4qi",
            ProvisioningParameters=[{
                'Key':'ManagedOrganizationalUnit',
                'Value': 'External (ou-tacd-hrb2mnda)',
                'UsePreviousValue': False,
            },
            {
                'Key':'SSOUserEmail',
                'Value':'SSOUserEmail@email.com',
                'UsePreviousValue': True
            },
            {
                'Key':'AccountEmail',
                'Value':aws_account_root_email,
                'UsePreviousValue': True
            },
            {
                'Key':'AccountName',
                'Value': 'AcountName',
                'UsePreviousValue': True
            },
            {
                'Key':'SSOUserFirstName',
                'Value':'SSOUserFirstName',
                'UsePreviousValue': True
            },
            {
                'Key':'SSOUserLastName',
                'Value':'SSOUserLastName',
                'UsePreviousValue': True
            }
            ])
        print(f"Account {aws_account_id} moved  to OU({destination_ou_id} )")
        if verbose:
            print(" move OU result is ",{response})
        
        return 1
    
        #except Exception as e:
        #    print(' An error has occured in operation ',e)
        #    return 0


    else:
        print(f"No provisioned product found for account {aws_account_id}")
    
def moveouandupdateawsaccountname(aws_account_id, aws_account_root_email,newtargetou, newaccountname, changeaccountname):
    """ 
    This function move the AWS Account (Provisioned product) from one parent Provsioned product to another )
    We can only move an AWS account from one OU to another, via the provisioned product method. 
    """ 

    provisioned_product = get_provisioned_product_detail(aws_account_id)

    #Guard - Check if the provisioned product is in good state
    # print(provisioned_product)

    if provisioned_product['Status'] =='UNDER_CHANGE':
        print('    Can not perform any operation as the status i', provisioned_product['Status'] )
        return 0

    
    print("-")
    # Get the provisioned product for the account
    provisioned_product_detail = service_catalog.describe_provisioned_product(
        Id=provisioned_product['Id']
    )
    # print(f"  Describe Provision  Product Detail : {provisioned_product_detail}")
    
    
    print("-")
    if provisioned_product:
                
        if provisioned_product:
            print(f"Provisioned Product Record Details:")
            provisioned_product['Id']
            print(f"  Name: {provisioned_product['Name']}")
            print(f"  Id: {provisioned_product['Id']}")
            print(f"  Status: {provisioned_product['Status']}")
            if verbose:
                print(f"  Full Provision  Product Detail : {provisioned_product}")
    
        else:
            print(f"Failed to retrieve provisioned product record details.") 
               
               
        # Set the product ID and provisioning artifact ID for the AWS Organizations product
        propvisioned_product_id = provisioned_product['Id'] 
        product_id = provisioned_product['ProductId'] # 'prod-a6orefazxydq4'  # Replace with the AWS Organizations product ID
        provisioning_artifact_id = provisioned_product['ProvisioningArtifactId']
        provisioning_artifact_name = provisioned_product['ProvisioningArtifactName']

        #try:
            # Check if the account is currently in the source OU
        print(f" Updating the AWS Account name for #  {aws_account_id}  to {newaccountname}")
        # Update the provisioned product to move the account to the destination OU
        print(f" Updating the AWS OU to #  {newtargetou}  ")
        
        response = service_catalog.update_provisioned_product(
            ProductId=product_id,
            ProvisionedProductId=propvisioned_product_id,
            ProvisioningArtifactName = provisioning_artifact_name,
            # ProvisioningArtifactId = provisioning_artifact_id,
            PathId= "lpv3-ncl5qh7lqv4qi",
            ProvisioningParameters=[{
                'Key':'ManagedOrganizationalUnit',
                'Value': newtargetou,
                'UsePreviousValue': False,
            },
            {
                'Key':'SSOUserEmail',
                'Value':'SSOUserEmail@email.com',
                'UsePreviousValue': True
            },
            {
                'Key':'AccountEmail',
                'Value':aws_account_root_email,
                'UsePreviousValue': True
            },
            {
                'Key':'AccountName',
                'Value': newaccountname,
                'UsePreviousValue': False
            },
            {
                'Key':'SSOUserFirstName',
                'Value':'SSOUserFirstName',
                'UsePreviousValue': True
            },
            {
                'Key':'SSOUserLastName',
                'Value':'SSOUserLastName',
                'UsePreviousValue': True
            }
            ])
        print(f"Account Name for {aws_account_id} Updated to ({newaccountname} )")
        if verbose:
            print(" move OU result is ",{response})
        
        return 1
    
        #except Exception as e:
        #    print(' An error has occured in operation ',e)
        #    return 0


    else:
        print(f"No provisioned product found for account {aws_account_id}")


def get_provisioned_product_detail(aws_account_id):
    """
    Retrieves the provisioned product ID for the given AWS account.
    
    Args:
        aws_account_id (str): The AWS account ID.
        
    Returns:
        str: The provisioned product ID, or None if not found.
    """
    
    # List the provisioned products
    try:
        response = service_catalog.search_provisioned_products(
            AccessLevelFilter={
                'Key': 'Account',
                'Value': 'self'
            },
            Filters={
                'SearchQuery' : [f'physicalId: {aws_account_id}']
            }
        )
        print(f' ---  Provissioned product detai for  AWS Account iD {aws_account_id}----')
        # print(response['ProvisionedProducts'][0])
        # Check if any provisioned products were found
        if response['ProvisionedProducts']:
            # Return the first provisioned product ID
            return response['ProvisionedProducts'][0]
        else:
            return 0
    except Exception as e:
            print(f"Error retrieving provisioned product details: {e}")
            return 0

def remove_from_org(aws_account_id):
    """
    Remove the account from the organization 
    """
    print(f"Account {aws_account_id} will be removed from organization. ")
    response = client_org.remove_account_from_organization(
        AccountId=aws_account_id
        )
    
    print(f"Account {aws_account_id} has been removed from organization. See the detail {response}")
    
def transfer_account_to_organization(source_organization_id, target_organization_id, account_id):
    """
    Transfers an AWS account from one organization to another.
    
    -> Leave the current organization 
    -> Change the email id of the AWS Account 
    -> Leave the Org
    
    
    Args:
        source_organization_id (str): The ID of the source organization.
        target_organization_id (str): The ID of the target organization.
        account_id (str): The ID of the AWS account to be transferred.
    """
    
    # Create an AWS Organizations client
    organizations = boto3.client('organizations')
    
    # Move the account to the parent organizational unit (OU) of the target organization
    response = organizations.move_account(
        AccountId=account_id,
        SourceParentId=source_organization_id,
        DestinationParentId=target_organization_id
    )
    
    print(f"Account {account_id} has been transferred from organization {source_organization_id} to organization {target_organization_id}. See the detail {response}")



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    cleanup_accounts_bulk_parser = subparsers.add_parser('cleanup')
    cleanup_accounts_bulk_parser.add_argument('--filename', required=True, help="Provide the file name")
    cleanup_accounts_bulk_parser.add_argument('--verbose', required=False, help="verbose detail about the program", default=True)
    cleanup_accounts_bulk_parser.set_defaults(func=cleanup_accounts_bulk)
        
    args = parser.parse_args()
    args.func(args)
