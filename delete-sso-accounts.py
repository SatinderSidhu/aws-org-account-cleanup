#Python program for AWS Identity store User and Group Management
import argparse
import json
import boto3
import csv

aws_region = 'us-east-1'

client_org =  boto3.client('organizations', 'account')
client_account =  boto3.client('account')
service_catalog = boto3.client('servicecatalog',region_name=aws_region)
client_sso =  boto3.client('sso-admin')

client_identitystore =  boto3.client('identitystore')


# reference https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/identitystore.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/identitystore/client/get_user_id.html


def delete_sso_accounts_bulk(args):
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
                IdentityStoreId = row['IdentityStoreId']
                ssoemail = row['ssoemail']
                
                print(' -- [',count,'] Deleting SSO User ' ,ssoemail)
                
                # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/identitystore/client/get_user_id.html
                

                # Get account detail 
                
                response_getuser_id = client_identitystore.get_user_id(
                    IdentityStoreId=IdentityStoreId,
                    AlternateIdentifier={
                        'UniqueAttribute': {
                            'AttributePath': 'emails.value',
                            'AttributeValue': ssoemail
                        }
                    }
                )
                
                UserId= response_getuser_id['UserId']
                
                if verbose:
                    print(response_getuser_id)
                    print('UserId: ', UserId)
                    
                    response_delete_user = client_identitystore.delete_user(
                       IdentityStoreId=IdentityStoreId,
                        UserId=UserId
                    )
                    
                    if response_delete_user:
                        print('Successfully deleted SSO user', ssoemail)
                
                else:
                    print(' No user exist with email id ', ssoemail)
                
                count = count+1
            except Exception as e:
                print(' An error has occured in operation ',e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    delete_sso_accounts_bulk_parser = subparsers.add_parser('delete_sso_accounts_bulk')
    delete_sso_accounts_bulk_parser.add_argument('--filename', required=True, help="Provide the file name")
    delete_sso_accounts_bulk_parser.add_argument('--verbose', required=False, help="verbose detail about the program", default=True)
    delete_sso_accounts_bulk_parser.set_defaults(func=delete_sso_accounts_bulk)
        
    args = parser.parse_args()
    args.func(args)
